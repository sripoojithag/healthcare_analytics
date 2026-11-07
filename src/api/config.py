"""
API Configuration Settings
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Healthcare Data Warehouse & Analytics Platform API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '../../healthcare_dw.db'))}"
    )
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "healthcare_platform_super_secret_jwt_hmac_key_2026"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    CORS_ORIGINS: list = ["*"]


settings = Settings()
