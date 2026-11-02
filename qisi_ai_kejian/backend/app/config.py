from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "qisi_ai_kejian"
    debug: bool = True
    mock_mode: bool = True  # never call real AI / WeChat / Pay
    database_path: str = str(Path(__file__).resolve().parent.parent / "data" / "qisi.db")
    cors_origins: list[str] = ["*"]
    # Placeholders for later Tencent / WeChat wiring
    wechat_app_id: str = "wx_mock_app_id"
    wechat_app_secret: str = "mock_secret"
    wechat_pay_mch_id: str = "mock_mch_id"
    default_mock_openid: str = "mock_openid_teacher_001"


settings = Settings()
