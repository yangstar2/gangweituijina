"""WeChat auth / pay placeholders — mock only for this slice."""

from __future__ import annotations

from typing import Any

from ..config import settings


def code_to_session(js_code: str) -> dict[str, Any]:
    """Mock wx.login code2session."""
    return {
        "openid": settings.default_mock_openid if not js_code else f"mock_{js_code[:8]}",
        "session_key": "mock_session_key",
        "unionid": None,
        "mock": True,
    }


def create_prepay(user_id: int, amount_fen: int, description: str) -> dict[str, Any]:
    """Mock WeChat Pay unified order — not calling real Pay API."""
    return {
        "mock": True,
        "user_id": user_id,
        "amount_fen": amount_fen,
        "description": description,
        "prepay_id": f"mock_prepay_{user_id}_{amount_fen}",
        "pay_sign_package": {
            "timeStamp": "0",
            "nonceStr": "mock_nonce",
            "package": "prepay_id=mock",
            "signType": "RSA",
            "paySign": "mock_sign",
        },
        "note": "Replace with real WeChat Pay when membership slice lands.",
    }
