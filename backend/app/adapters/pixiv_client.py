"""Pixiv 访问支持"""

import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class PixivClient:
    """Pixiv 访问管理"""

    def __init__(self) -> None:
        """准备访问状态"""
        self._api: Optional[object] = None
        self._token: Optional[str] = None

    def ensure(self) -> bool:
        """准备访问工具"""
        refresh_token = settings.PIXIV_REFRESH_TOKEN
        if not refresh_token:
            logger.warning("Pixiv: no refresh token configured")
            self._api = None
            self._token = None
            return False
        if self._api is not None and self._token == refresh_token:
            return True

        try:
            from pixivpy3 import AppPixivAPI

            api = AppPixivAPI()
            api.auth(refresh_token=refresh_token)
            self._api = api
            self._token = refresh_token
            logger.info("Pixiv API authenticated successfully")
            return True
        except ImportError:
            logger.warning("Pixiv: pixivpy3 not installed. Run: pip install pixivpy3")
            return False
        except Exception:
            logger.exception("Pixiv authentication failed")
            self._api = None
            return False

    def api(self) -> Optional[object]:
        """取出访问工具"""
        return self._api
