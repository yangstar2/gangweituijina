"""WeChat auth / pay placeholders — mock only; fill real credentials later."""

from __future__ import annotations

from typing import Any

from ..config import settings


def code_to_session(js_code: str) -> dict[str, Any]:
    """Mock wx.login code2session.

    Real fill-in:
      POST https://api.weixin.qq.com/sns/jscode2session
      appid=WECHAT_APP_ID&secret=WECHAT_APP_SECRET&js_code=...&grant_type=authorization_code
    """
    return {
        "openid": settings.default_mock_openid if not js_code else f"mock_{js_code[:8]}",
        "session_key": "mock_session_key",
        "unionid": None,
        "mock": True,
        "placeholder": {
            "wechat_app_id": settings.wechat_app_id,
            "wechat_app_secret": "***set WECHAT_APP_SECRET***",
        },
    }


def create_prepay(
    user_id: int,
    amount_fen: int,
    description: str,
    out_trade_no: str,
    openid: str,
) -> dict[str, Any]:
    """Mock JSAPI unified order.

    Real fill-in (APIv3):
      mchid / certificate serial / private key / APIv3 key
      notify_url → /api/pay/notify/wechat
    """
    prepay_id = f"mock_prepay_{out_trade_no}"
    return {
        "mock": True,
        "user_id": user_id,
        "openid": openid,
        "amount_fen": amount_fen,
        "description": description,
        "out_trade_no": out_trade_no,
        "prepay_id": prepay_id,
        "mch_id": settings.wechat_pay_mch_id,
        "pay_sign_package": {
            "appId": settings.wechat_app_id,
            "timeStamp": "1710000000",
            "nonceStr": "mock_nonce",
            "package": f"prepay_id={prepay_id}",
            "signType": "RSA",
            "paySign": "mock_sign_replace_me",
        },
        "note": "Set WECHAT_PAY_MCH_ID / certs / APIv3 key; replace this mock.",
    }


def verify_notify_signature(headers: dict[str, str], body: bytes) -> bool:
    """Mock notify signature check — always true in mock_mode."""
    _ = headers, body
    return True


def parse_notify_resource(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract trade fields from (mock) notify body."""
    return {
        "out_trade_no": payload.get("out_trade_no") or payload.get("order_id"),
        "transaction_id": payload.get("transaction_id") or f"mock_txn_{payload.get('order_id')}",
        "trade_state": payload.get("trade_state") or "SUCCESS",
    }
