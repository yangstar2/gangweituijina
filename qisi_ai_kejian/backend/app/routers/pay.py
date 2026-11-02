"""Mock WeChat Pay — create order / prepay / notify stubs."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..db import dumps, get_conn, utcnow
from ..services import membership as membership_svc
from ..services import mock_wechat

router = APIRouter(prefix="/api/pay", tags=["pay"])


class CreateOrderIn(BaseModel):
    user_id: int
    plan_id: str = Field(..., description="pro_month | pro_year")


class OrderOut(BaseModel):
    id: int
    user_id: int
    plan_id: str
    amount_fen: int
    status: str
    wx_prepay_id: str | None
    pay_sign_package: dict | None = None
    created_at: str
    mock: bool = True


class MockNotifyIn(BaseModel):
    order_id: int


def _order_out(row, pay_sign_package: dict | None = None) -> OrderOut:
    return OrderOut(
        id=row["id"],
        user_id=row["user_id"],
        plan_id=row["plan_id"],
        amount_fen=row["amount_fen"],
        status=row["status"],
        wx_prepay_id=row["wx_prepay_id"],
        pay_sign_package=pay_sign_package,
        created_at=row["created_at"],
        mock=True,
    )


@router.post("/orders", response_model=OrderOut)
def create_order(body: CreateOrderIn) -> OrderOut:
    plan = membership_svc.get_plan(body.plan_id)
    if not plan or not plan.get("premium"):
        raise HTTPException(400, "plan_id must be a paid plan (pro_month / pro_year)")
    if plan["price_fen"] <= 0:
        raise HTTPException(400, "invalid plan price")

    now = utcnow()
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, openid FROM users WHERE id = ?", (body.user_id,)
        ).fetchone()
        if not user:
            raise HTTPException(404, "user not found")

        cur = conn.execute(
            """
            INSERT INTO pay_orders
              (user_id, plan_id, amount_fen, status, wx_prepay_id, created_at, updated_at)
            VALUES (?, ?, ?, 'mock_pending', NULL, ?, ?)
            """,
            (body.user_id, body.plan_id, plan["price_fen"], now, now),
        )
        order_id = cur.lastrowid
        out_trade_no = f"QISI{order_id:08d}"
        prepay = mock_wechat.create_prepay(
            user_id=body.user_id,
            amount_fen=plan["price_fen"],
            description=f"奇思会员-{plan['name']}",
            out_trade_no=out_trade_no,
            openid=user["openid"],
        )
        conn.execute(
            "UPDATE pay_orders SET wx_prepay_id=?, updated_at=? WHERE id=?",
            (prepay["prepay_id"], now, order_id),
        )
        row = conn.execute("SELECT * FROM pay_orders WHERE id = ?", (order_id,)).fetchone()

    return _order_out(row, pay_sign_package=prepay["pay_sign_package"])


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int) -> OrderOut:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM pay_orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        raise HTTPException(404, "order not found")
    return _order_out(row)


@router.post("/notify/mock", response_model=OrderOut)
def mock_notify(body: MockNotifyIn) -> OrderOut:
    """Dev helper: simulate successful WeChat Pay callback."""
    return _mark_paid(body.order_id, transaction_id=f"mock_txn_{body.order_id}", payload={"mock": True})


@router.post("/notify/wechat")
async def wechat_notify(request: Request) -> dict:
    """Placeholder for real WeChat Pay v3 notify.

    Fill-in: verify Wechatpay-Signature, decrypt resource, then mark paid.
    """
    raw = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    if not mock_wechat.verify_notify_signature(headers, raw):
        raise HTTPException(401, "invalid signature")
    try:
        payload = json.loads(raw.decode() or "{}")
    except json.JSONDecodeError:
        payload = {}
    parsed = mock_wechat.parse_notify_resource(payload)
    out_trade_no = str(parsed.get("out_trade_no") or "")
    # out_trade_no format QISI00000012
    if not out_trade_no.startswith("QISI"):
        # also accept {"order_id": N} in mock
        order_id = payload.get("order_id")
        if not order_id:
            raise HTTPException(400, "missing out_trade_no")
    else:
        order_id = int(out_trade_no.replace("QISI", ""))
    _mark_paid(int(order_id), transaction_id=parsed.get("transaction_id"), payload=payload)
    return {"code": "SUCCESS", "message": "成功"}


def _mark_paid(order_id: int, transaction_id: str | None, payload: dict) -> OrderOut:
    now = utcnow()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM pay_orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(404, "order not found")
        if row["status"] == "paid":
            return _order_out(row)

        conn.execute(
            """
            UPDATE pay_orders
            SET status='paid', wx_transaction_id=?, notify_payload=?, paid_at=?, updated_at=?
            WHERE id=?
            """,
            (transaction_id, dumps(payload), now, now, order_id),
        )

        member = conn.execute(
            "SELECT plan, expires_at FROM members WHERE user_id = ?", (row["user_id"],)
        ).fetchone()
        cur_plan = member["plan"] if member else "free"
        cur_exp = member["expires_at"] if member else None
        new_plan, new_exp = membership_svc.extend_membership(cur_plan, cur_exp, row["plan_id"])
        if member:
            conn.execute(
                "UPDATE members SET plan=?, expires_at=? WHERE user_id=?",
                (new_plan, new_exp, row["user_id"]),
            )
        else:
            conn.execute(
                "INSERT INTO members (user_id, plan, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (row["user_id"], new_plan, new_exp, now),
            )

        row = conn.execute("SELECT * FROM pay_orders WHERE id = ?", (order_id,)).fetchone()
    return _order_out(row)
