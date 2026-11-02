from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import get_conn, utcnow
from ..services import membership as membership_svc

router = APIRouter(prefix="/api/membership", tags=["membership"])


class PlanOut(BaseModel):
    id: str
    name: str
    price_fen: int
    duration_days: int | None
    description: str
    features: list[str]
    premium: bool


class MembershipOut(BaseModel):
    user_id: int
    plan: str
    plan_name: str
    expires_at: str | None
    is_premium_active: bool
    premium_models: list[str]


@router.get("/plans", response_model=list[PlanOut])
def plans() -> list[PlanOut]:
    return [PlanOut(**p) for p in membership_svc.list_plans()]


@router.get("/me", response_model=MembershipOut)
def me(user_id: int = Query(...)) -> MembershipOut:
    with get_conn() as conn:
        user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(404, "user not found")
        row = conn.execute(
            "SELECT plan, expires_at FROM members WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            now = utcnow()
            conn.execute(
                "INSERT INTO members (user_id, plan, expires_at, created_at) VALUES (?, 'free', NULL, ?)",
                (user_id, now),
            )
            plan, expires = "free", None
        else:
            plan, expires = row["plan"], row["expires_at"]

    plan_info = membership_svc.get_plan(plan) or membership_svc.get_plan("free")
    return MembershipOut(
        user_id=user_id,
        plan=plan,
        plan_name=plan_info["name"] if plan_info else plan,
        expires_at=expires,
        is_premium_active=membership_svc.plan_active(plan, expires),
        premium_models=sorted(membership_svc.PREMIUM_MODELS),
    )
