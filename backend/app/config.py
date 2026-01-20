"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./soyosaki.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Adapter concurrency (per adapter pool)
    ADAPTER_MAX_WORKERS: int = 8

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
    LOFTER_DYNAMIC_ENABLED: bool = False  # enable Playwright crawling
    LOFTER_DYNAMIC_HEADLESS: bool = True  # headless browser for Playwright
    LOFTER_DYNAMIC_MAX_ITEMS: int = 30  # per-search target items
    LOFTER_DYNAMIC_MAX_SCROLLS: int = 8  # max scrolls per crawl
    LOFTER_DYNAMIC_SCROLL_WAIT_MS: int = 1200  # wait after each scroll
    LOFTER_DYNAMIC_INITIAL_WAIT_MS: int = 1500  # initial load wait
    LOFTER_MAX_PAGE_SIZE: int = 30
    LOFTER_DYNAMIC_CACHE_TTL: int = 300

    # Bilibili (optional)
    BILIBILI_SESSDATA: str = ""  # 登录 cookie，可选

    # Reading history
    READING_HISTORY_TTL_DAYS: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
