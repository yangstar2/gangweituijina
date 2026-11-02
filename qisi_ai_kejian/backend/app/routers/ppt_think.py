"""PPT content thinking via DeepSeek, then optional generate hook."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..db import dumps, get_conn, loads, utcnow
from ..schemas.common import OutlineOut
from ..services import deepseek, membership as membership_svc, mock_ai
from .generate import ArtifactOut, _row_to_artifact

router = APIRouter(prefix="/api/sessions", tags=["ppt-think"])


class PptThinkIn(BaseModel):
    style_id: str = "clean_academic"
    model_id: str = "mock-qisi-lite"
    title: str | None = None
    auto_generate: bool = False


class ThinkingStepOut(BaseModel):
    title: str
    detail: str


class PptThinkOut(BaseModel):
    session_id: int
    provider: str
    model: str
    thinking: str
    thinking_steps: list[ThinkingStepOut]
    outline: OutlineOut
    used_mock_fallback: bool = False
    deepseek_configured: bool = False
    artifact: ArtifactOut | None = None
    error: str | None = None


def _get_outline_dict(conn, session_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM outlines WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not row:
        return None
    return {
        "key_points": loads(row["key_points"], []),
        "outline": loads(row["outline"], []),
        "notes": loads(row["notes"], []),
        "raw_summary": row["raw_summary"],
    }


def _upsert_outline(conn, session_id: int, ol: dict, now: str) -> OutlineOut:
    existing = conn.execute(
        "SELECT id FROM outlines WHERE session_id = ?", (session_id,)
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE outlines SET key_points=?, outline=?, notes=?, raw_summary=?, updated_at=?
            WHERE session_id=?
            """,
            (
                dumps(ol["key_points"]),
                dumps(ol["outline"]),
                dumps(ol["notes"]),
                ol.get("raw_summary"),
                now,
                session_id,
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO outlines (session_id, key_points, outline, notes, raw_summary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                dumps(ol["key_points"]),
                dumps(ol["outline"]),
                dumps(ol["notes"]),
                ol.get("raw_summary"),
                now,
                now,
            ),
        )
    conn.execute(
        "UPDATE sessions SET status='outlined', updated_at=? WHERE id=?",
        (now, session_id),
    )
    return OutlineOut(
        session_id=session_id,
        key_points=ol["key_points"],
        outline=ol["outline"],
        notes=ol["notes"],
        raw_summary=ol.get("raw_summary"),
    )


def _maybe_generate(
    conn,
    session,
    session_id: int,
    outline: dict,
    body: PptThinkIn,
    now: str,
) -> ArtifactOut | None:
    if not body.auto_generate:
        return None
    content_type = session["content_type"]
    if content_type != "courseware":
        return None

    member = conn.execute(
        "SELECT plan, expires_at FROM members WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()
    plan = member["plan"] if member else "free"
    expires = member["expires_at"] if member else None
    ok, reason = membership_svc.can_use_model(plan, expires, body.model_id)
    if not ok:
        raise HTTPException(
            status_code=402,
            detail={"message": reason, "code": "membership_required", "plan": plan},
        )

    title = body.title or session["title"]
    content = mock_ai.generate_ppt(outline, body.style_id, body.model_id, title)
    # Annotate provenance without exposing secrets
    content["thinking_provider"] = "deepseek" if deepseek.is_configured() else "mock"
    cur = conn.execute(
        """
        INSERT INTO artifacts (session_id, artifact_type, style_id, model_id, title, content, status, created_at)
        VALUES (?, 'ppt', ?, ?, ?, ?, 'ready', ?)
        """,
        (
            session_id,
            body.style_id,
            body.model_id,
            content.get("title") or title,
            dumps(content),
            now,
        ),
    )
    artifact_id = cur.lastrowid
    conn.execute(
        "UPDATE sessions SET status='done', updated_at=? WHERE id=?",
        (now, session_id),
    )
    row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    return _row_to_artifact(row)


@router.post("/{session_id}/ppt-think", response_model=PptThinkOut)
def ppt_think(session_id: int, body: PptThinkIn | None = None) -> PptThinkOut:
    """DeepSeek reasoning + structured PPT outline; optional auto generate."""
    body = body or PptThinkIn()
    now = utcnow()
    with get_conn() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(404, "session not found")
        if session["content_type"] != "courseware":
            raise HTTPException(400, "ppt-think is only for courseware sessions")

        history_rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
        existing = _get_outline_dict(conn, session_id)

        result = deepseek.think_ppt_content(
            session["content_type"], history, existing
        )
        outline_out = _upsert_outline(conn, session_id, result.outline, now)
        artifact = _maybe_generate(conn, session, session_id, result.outline, body, now)

    return PptThinkOut(
        session_id=session_id,
        provider=result.provider,
        model=result.model,
        thinking=result.thinking,
        thinking_steps=[ThinkingStepOut(**s) for s in result.thinking_steps],
        outline=outline_out,
        used_mock_fallback=result.used_mock_fallback,
        deepseek_configured=deepseek.is_configured(),
        artifact=artifact,
        error=result.error,
    )


@router.post("/{session_id}/ppt-think/stream")
def ppt_think_stream(session_id: int, body: PptThinkIn | None = None):
    """NDJSON stream: step events, then final thinking + outline (+ optional artifact).

    Miniprogram may prefer the non-stream endpoint; this helps progressive UIs.
    """
    body = body or PptThinkIn()

    def event_iter():
        now = utcnow()
        with get_conn() as conn:
            session = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not session:
                yield json.dumps({"event": "error", "detail": "session not found"}) + "\n"
                return
            if session["content_type"] != "courseware":
                yield json.dumps(
                    {"event": "error", "detail": "ppt-think is only for courseware sessions"}
                ) + "\n"
                return

            yield json.dumps(
                {
                    "event": "start",
                    "deepseek_configured": deepseek.is_configured(),
                    "session_id": session_id,
                }
            ) + "\n"

            history_rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
            history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
            existing = _get_outline_dict(conn, session_id)

            yield json.dumps(
                {"event": "status", "message": "正在调用推理模型…"}
            ) + "\n"

            result = deepseek.think_ppt_content(
                session["content_type"], history, existing
            )

            for i, step in enumerate(result.thinking_steps):
                yield json.dumps(
                    {
                        "event": "step",
                        "index": i,
                        "title": step.get("title"),
                        "detail": step.get("detail"),
                    }
                ) + "\n"

            outline_out = _upsert_outline(conn, session_id, result.outline, now)
            try:
                artifact = _maybe_generate(
                    conn, session, session_id, result.outline, body, now
                )
            except HTTPException as exc:
                yield json.dumps(
                    {"event": "error", "detail": exc.detail, "status": exc.status_code}
                ) + "\n"
                return

            payload = {
                "event": "done",
                "provider": result.provider,
                "model": result.model,
                "thinking": result.thinking,
                "thinking_steps": result.thinking_steps,
                "outline": outline_out.model_dump(),
                "used_mock_fallback": result.used_mock_fallback,
                "deepseek_configured": deepseek.is_configured(),
                "artifact": artifact.model_dump() if artifact else None,
                "error": result.error,
            }
            yield json.dumps(payload, ensure_ascii=False) + "\n"

    return StreamingResponse(event_iter(), media_type="application/x-ndjson")
