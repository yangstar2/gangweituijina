from fastapi import APIRouter
from pydantic import BaseModel

from ..db import get_conn, utcnow
from ..services import mock_wechat

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    code: str = "mock_code"


class LoginOut(BaseModel):
    user_id: int
    openid: str
    nickname: str
    member_plan: str
    mock: bool = True


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    """Mock WeChat mini-program login."""
    session = mock_wechat.code_to_session(body.code)
    openid = session["openid"]
    now = utcnow()
    with get_conn() as conn:
        row = conn.execute("SELECT id, nickname FROM users WHERE openid = ?", (openid,)).fetchone()
        if row:
            user_id = row["id"]
            nickname = row["nickname"] or "老师"
        else:
            cur = conn.execute(
                "INSERT INTO users (openid, nickname, avatar_url, created_at) VALUES (?, ?, ?, ?)",
                (openid, "老师", None, now),
            )
            user_id = cur.lastrowid
            nickname = "老师"
            conn.execute(
                "INSERT INTO members (user_id, plan, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (user_id, "free", None, now),
            )
        member = conn.execute(
            "SELECT plan FROM members WHERE user_id = ?", (user_id,)
        ).fetchone()
    return LoginOut(
        user_id=user_id,
        openid=openid,
        nickname=nickname or "老师",
        member_plan=member["plan"] if member else "free",
        mock=True,
    )
