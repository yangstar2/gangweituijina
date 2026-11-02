from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "qisi_ai_kejian"
    debug: bool = True
    mock_mode: bool = True  # WeChat / Pay stay mocked; DeepSeek uses its own key gate
    database_path: str = str(_BACKEND_DIR / "data" / "qisi.db")
    cors_origins: list[str] = ["*"]
    # Placeholders — override via env (WECHAT_APP_ID, …); never commit real secrets
    wechat_app_id: str = "wx_mock_app_id"
    wechat_app_secret: str = "mock_secret"
    wechat_pay_mch_id: str = "mock_mch_id"
    wechat_pay_api_v3_key: str = "mock_api_v3_key"
    wechat_pay_cert_serial: str = "mock_cert_serial"
    wechat_pay_notify_url: str = "https://YOUR_DOMAIN/api/pay/notify/wechat"
    admin_username: str = "admin"
    admin_password: str = "admin_mock_change_me"
    default_mock_openid: str = "mock_openid_teacher_001"
    # DeepSeek (OpenAI-compatible). Empty key → mock thinking fallback for CI/dev.
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-reasoner"
    deepseek_fallback_model: str = "deepseek-chat"
    deepseek_timeout_sec: float = 90.0


settings = Settings()
