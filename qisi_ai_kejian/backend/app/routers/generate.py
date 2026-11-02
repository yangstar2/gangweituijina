"""Full PPT / exam generation from clarified outline (mock AI)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db import dumps, get_conn, loads, utcnow
from ..schemas.common import OutlineOut
from ..services import mock_ai

router = APIRouter(prefix="/api/sessions", tags=["generate"])


class GenerateIn(BaseModel):
    style_id: str = "clean_academic"
    model_id: str = "mock-qisi-lite"
    title: str | None = None
    # optional override; default from session content_type
    artifact_type: str | None = Field(
        default=None, description="ppt | exam; default inferred from session"
    )


class ArtifactOut(BaseModel):
    id: int
    session_id: int
    artifact_type: str
    style_id: str
    model_id: str
    title: str | None
    status: str
    content: dict
    created_at: str


def _get_outline(conn, session_id: int) -> OutlineOut | None:
    row = conn.execute(
        "SELECT * FROM outlines WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not row:
        return None
    return OutlineOut(
        session_id=session_id,
        key_points=loads(row["key_points"], []),
        outline=loads(row["outline"], []),
        notes=loads(row["notes"], []),
        raw_summary=row["raw_summary"],
    )


def _row_to_artifact(row) -> ArtifactOut:
    return ArtifactOut(
        id=row["id"],
        session_id=row["session_id"],
        artifact_type=row["artifact_type"],
        style_id=row["style_id"],
        model_id=row["model_id"],
        title=row["title"],
        status=row["status"],
        content=loads(row["content"], {}),
        created_at=row["created_at"],
    )


@router.post("/{session_id}/generate", response_model=ArtifactOut)
def generate_artifact(session_id: int, body: GenerateIn) -> ArtifactOut:
    """Generate full PPT or exam paper from outline. Mock only — no real model call."""
    now = utcnow()
    with get_conn() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(404, "session not found")
        ol = _get_outline(conn, session_id)
        if not ol:
            raise HTTPException(400, "outline required before generate")

        content_type = session["content_type"]
        artifact_type = body.artifact_type or ("ppt" if content_type == "courseware" else "exam")
        if artifact_type not in ("ppt", "exam"):
            raise HTTPException(400, "artifact_type must be ppt or exam")

        outline_payload = {
            "key_points": ol.key_points,
            "outline": ol.outline,
            "notes": ol.notes,
            "raw_summary": ol.raw_summary,
        }
        title = body.title or session["title"]

        if artifact_type == "ppt":
            content = mock_ai.generate_ppt(outline_payload, body.style_id, body.model_id, title)
        else:
            content = mock_ai.generate_exam(
                outline_payload, body.style_id, body.model_id, title, textbook_hint=ol.raw_summary
            )

        cur = conn.execute(
            """
            INSERT INTO artifacts (session_id, artifact_type, style_id, model_id, title, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ready', ?)
            """,
            (
                session_id,
                artifact_type,
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


@router.get("/{session_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(session_id: int) -> list[ArtifactOut]:
    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "session not found")
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE session_id = ? ORDER BY id DESC",
            (session_id,),
        ).fetchall()
    return [_row_to_artifact(r) for r in rows]


artifacts_router = APIRouter(prefix="/api/artifacts", tags=["generate"])


@artifacts_router.get("/{artifact_id}", response_model=ArtifactOut)
def get_artifact(artifact_id: int) -> ArtifactOut:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        raise HTTPException(404, "artifact not found")
    return _row_to_artifact(row)
