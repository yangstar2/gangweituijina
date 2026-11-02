from fastapi import APIRouter, HTTPException

from ..config import settings
from ..db import dumps, get_conn, loads, row_to_dict, utcnow
from ..schemas import (
    ChatMessageIn,
    ChatReplyOut,
    OutlineOut,
    PreviewOut,
    PreviewPage,
    SessionCreate,
    SessionOut,
    TeacherTurnOut,
)
from ..services import mock_ai, teacher_prep

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _ensure_user(conn, openid: str) -> int:
    row = conn.execute("SELECT id FROM users WHERE openid = ?", (openid,)).fetchone()
    if row:
        return row["id"]
    now = utcnow()
    cur = conn.execute(
        "INSERT INTO users (openid, nickname, avatar_url, created_at) VALUES (?, ?, ?, ?)",
        (openid, "老师", None, now),
    )
    user_id = cur.lastrowid
    conn.execute(
        "INSERT INTO members (user_id, plan, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (user_id, "free", None, now),
    )
    return user_id


def _session_out(row) -> SessionOut:
    d = row_to_dict(row)
    return SessionOut(
        id=d["id"],
        content_type=d["content_type"],
        title=d["title"],
        status=d["status"],
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )


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


@router.post("", response_model=SessionOut)
def create_session(body: SessionCreate) -> SessionOut:
    openid = body.openid or settings.default_mock_openid
    now = utcnow()
    title = body.title or ("新课件澄清" if body.content_type == "courseware" else "新试卷澄清")
    with get_conn() as conn:
        user_id = _ensure_user(conn, openid)
        cur = conn.execute(
            """
            INSERT INTO sessions (user_id, content_type, title, status, created_at, updated_at)
            VALUES (?, ?, ?, 'clarifying', ?, ?)
            """,
            (user_id, body.content_type, title, now, now),
        )
        session_id = cur.lastrowid
        # Seed teacher greeting
        greeting = (
            "你好，我是「追问老师」。生成前我们先对齐内容。"
            "请用一两句话说明你想做的课件或试卷主题。"
        )
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, 'teacher', ?, ?)",
            (session_id, greeting, now),
        )
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _session_out(row)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int) -> SessionOut:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(404, "session not found")
    return _session_out(row)


@router.get("/{session_id}/messages")
def list_messages(session_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{session_id}/messages", response_model=ChatReplyOut)
def post_message(session_id: int, body: ChatMessageIn) -> ChatReplyOut:
    now = utcnow()
    with get_conn() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(404, "session not found")

        cur = conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (session_id, body.content, now),
        )
        user_msg_id = cur.lastrowid

        history_rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        # Exclude the just-inserted user message from history for the mock (passed separately)
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows[:-1]]

        turn = mock_ai.teacher_reply(session["content_type"], history, body.content)
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, 'teacher', ?, ?)",
            (session_id, turn["content"], now),
        )

        outline_out = None
        status = session["status"]
        if turn.get("outline"):
            ol = turn["outline"]
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
            status = "outlined"
            conn.execute(
                "UPDATE sessions SET status=?, updated_at=? WHERE id=?",
                (status, now, session_id),
            )
            outline_out = OutlineOut(
                session_id=session_id,
                key_points=ol["key_points"],
                outline=ol["outline"],
                notes=ol["notes"],
                raw_summary=ol.get("raw_summary"),
            )
        else:
            conn.execute(
                "UPDATE sessions SET updated_at=? WHERE id=?",
                (now, session_id),
            )

    return ChatReplyOut(
        user_message_id=user_msg_id,
        teacher=TeacherTurnOut(
            content=turn["content"],
            clarifying_done=bool(turn.get("clarifying_done")),
            suggested_replies=turn.get("suggested_replies") or [],
        ),
        session_status=status,
        outline=outline_out,
    )


@router.get("/{session_id}/outline", response_model=OutlineOut)
def get_outline(session_id: int) -> OutlineOut:
    with get_conn() as conn:
        ol = _get_outline(conn, session_id)
    if not ol:
        raise HTTPException(404, "outline not ready")
    return ol


@router.post("/{session_id}/preview", response_model=PreviewOut)
def create_preview(
    session_id: int,
    style_id: str = "clean_academic",
    model_id: str = "mock-qisi-lite",
) -> PreviewOut:
    now = utcnow()
    with get_conn() as conn:
        session = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(404, "session not found")
        ol = _get_outline(conn, session_id)
        if not ol:
            raise HTTPException(400, "outline required before preview")

        outline_payload = {
            "key_points": ol.key_points,
            "outline": ol.outline,
            "notes": ol.notes,
            "raw_summary": ol.raw_summary,
        }
        if session["content_type"] == "courseware" and teacher_prep.is_available():
            history_rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
            history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
            ctx = teacher_prep.resolve_skill_context(history, session["title"])
            deck = teacher_prep.local_skill_slides(
                outline_payload, style_id, model_id, session["title"], ctx
            )
            pages = teacher_prep.slides_to_preview_pages(deck.get("slides") or [], limit=6)
        else:
            pages = mock_ai.build_preview(
                session["content_type"],
                outline_payload,
                style_id,
                model_id,
            )
        conn.execute(
            """
            INSERT INTO previews (session_id, style_id, model_id, pages, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, style_id, model_id, dumps(pages), now),
        )
        conn.execute(
            "UPDATE sessions SET status='previewing', updated_at=? WHERE id=?",
            (now, session_id),
        )

    return PreviewOut(
        session_id=session_id,
        style_id=style_id,
        model_id=model_id,
        pages=[PreviewPage(**p) for p in pages],
    )
