"""Membership plans + entitlement checks (SQLite-backed, mock pay)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

PLANS: list[dict[str, Any]] = [
    {
        "id": "free",
        "name": "免费版",
        "price_fen": 0,
        "duration_days": None,
        "description": "澄清 + 6 页预览；正式生成仅限奇思 Lite",
        "features": ["追问老师", "大纲与预览", "Lite 模型生成"],
        "premium": False,
    },
    {
        "id": "pro_month",
        "name": "专业月卡",
        "price_fen": 2900,
        "duration_days": 30,
        "description": "全模型正式生成 PPT / 试卷",
        "features": ["全部 mock 模型", "无限次正式生成", "优先队列（占位）"],
        "premium": True,
    },
    {
        "id": "pro_year",
        "name": "专业年卡",
        "price_fen": 19900,
        "duration_days": 365,
        "description": "年付更优惠，权益同月卡",
        "features": ["全部 mock 模型", "无限次正式生成", "年付优惠"],
        "premium": True,
    },
]

# Models that require an active premium plan for *full generate*
PREMIUM_MODELS = {"mock-hunyuan", "mock-deepseek"}


def list_plans() -> list[dict[str, Any]]:
    return PLANS


def get_plan(plan_id: str) -> dict[str, Any] | None:
    return next((p for p in PLANS if p["id"] == plan_id), None)


def is_premium_plan(plan_id: str) -> bool:
    p = get_plan(plan_id)
    return bool(p and p.get("premium"))


def plan_active(plan: str, expires_at: str | None) -> bool:
    if not is_premium_plan(plan):
        return False
    if not expires_at:
        return True
    try:
        exp = datetime.fromisoformat(expires_at)
    except ValueError:
        return False
    now = datetime.now(timezone.utc)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp > now


def can_use_model(plan: str, expires_at: str | None, model_id: str) -> tuple[bool, str | None]:
    """Return (ok, error_message). Free may use non-premium models only."""
    if model_id not in PREMIUM_MODELS:
        return True, None
    if plan_active(plan, expires_at):
        return True, None
    return False, "该模型需要专业会员，请先开通会员后再生成"


def extend_membership(current_plan: str, expires_at: str | None, new_plan_id: str) -> tuple[str, str]:
    plan = get_plan(new_plan_id)
    if not plan or not plan.get("premium"):
        raise ValueError("invalid premium plan")
    days = int(plan["duration_days"] or 30)
    now = datetime.now(timezone.utc)
    base = now
    if plan_active(current_plan, expires_at) and expires_at:
        try:
            cur_exp = datetime.fromisoformat(expires_at)
            if cur_exp.tzinfo is None:
                cur_exp = cur_exp.replace(tzinfo=timezone.utc)
            if cur_exp > now:
                base = cur_exp
        except ValueError:
            pass
    new_exp = base + timedelta(days=days)
    return new_plan_id, new_exp.isoformat()
