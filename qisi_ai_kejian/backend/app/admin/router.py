from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..db import get_conn, loads
from .auth import require_admin

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["tojson_pretty"] = lambda v: json.dumps(v, ensure_ascii=False, indent=2)

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)


@router.get("", response_class=HTMLResponse)
def admin_root(_: str = Depends(require_admin)) -> RedirectResponse:
    return RedirectResponse(url="/admin/members", status_code=302)


@router.get("/members", response_class=HTMLResponse)
def members_page(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.id AS user_id, u.openid, u.nickname, u.created_at AS user_created,
                   m.plan, m.expires_at, m.created_at AS member_since
            FROM users u
            LEFT JOIN members m ON m.user_id = u.id
            ORDER BY u.id DESC
            """
        ).fetchall()
    return templates.TemplateResponse(
        "members.html",
        {
            "request": request,
            "title": "会员列表",
            "active": "members",
            "rows": [dict(r) for r in rows],
        },
    )


@router.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT o.id, o.user_id, u.nickname, u.openid, o.plan_id, o.amount_fen,
                   o.status, o.wx_prepay_id, o.wx_transaction_id, o.paid_at, o.created_at
            FROM pay_orders o
            LEFT JOIN users u ON u.id = o.user_id
            ORDER BY o.id DESC
            """
        ).fetchall()
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "title": "支付订单",
            "active": "orders",
            "rows": [dict(r) for r in rows],
        },
    )


@router.get("/sessions", response_class=HTMLResponse)
def sessions_page(request: Request, _: str = Depends(require_admin)) -> HTMLResponse:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.user_id, u.nickname, s.content_type, s.title, s.status,
                   s.created_at, s.updated_at,
                   (SELECT COUNT(*) FROM artifacts a WHERE a.session_id = s.id) AS artifact_count
            FROM sessions s
            LEFT JOIN users u ON u.id = s.user_id
            ORDER BY s.id DESC
            LIMIT 200
            """
        ).fetchall()
    return templates.TemplateResponse(
        "sessions.html",
        {
            "request": request,
            "title": "生成会话",
            "active": "sessions",
            "rows": [dict(r) for r in rows],
        },
    )


@router.get("/artifacts/{artifact_id}", response_class=HTMLResponse)
def artifact_page(
    request: Request, artifact_id: int, _: str = Depends(require_admin)
) -> HTMLResponse:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        return templates.TemplateResponse(
            "artifact.html",
            {"request": request, "title": "未找到", "active": "sessions", "artifact": None},
            status_code=404,
        )
    data = dict(row)
    data["content_obj"] = loads(data["content"], {})
    return templates.TemplateResponse(
        "artifact.html",
        {"request": request, "title": f"产物 #{artifact_id}", "active": "sessions", "artifact": data},
    )
