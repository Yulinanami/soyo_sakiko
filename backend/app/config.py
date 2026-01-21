"""应用配置"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./soyosaki.db"

    LOG_LEVEL: str = "INFO"

    ADAPTER_MAX_WORKERS: int = 8

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365  # 365天登录有效期

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    PIXIV_REFRESH_TOKEN: str = ""

    LOFTER_COOKIE: str = ""
    LOFTER_CAPTTOKEN: str = ""
    LOFTER_DYNAMIC_ENABLED: bool = False
    LOFTER_DYNAMIC_HEADLESS: bool = True
    LOFTER_DYNAMIC_MAX_ITEMS: int = 30
    LOFTER_DYNAMIC_MAX_SCROLLS: int = 8
    LOFTER_DYNAMIC_SCROLL_WAIT_MS: int = 1200
    LOFTER_DYNAMIC_INITIAL_WAIT_MS: int = 1500
    LOFTER_MAX_PAGE_SIZE: int = 30
    LOFTER_DYNAMIC_CACHE_TTL: int = 300

    BILIBILI_SESSDATA: str = ""  # 登录信息，可选

    READING_HISTORY_TTL_DAYS: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
