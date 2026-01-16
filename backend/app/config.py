"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./soyosaki.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Pixiv (optional)
    PIXIV_REFRESH_TOKEN: str = ""

    # Lofter (optional) - requires login cookie
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

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
