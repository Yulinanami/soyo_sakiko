"""Bilibili 访问支持"""

import logging
import uuid
from typing import Optional, List, Dict, Any, Tuple
from app.config import settings
from app.services.http_client import get_no_proxy_sync_client

logger = logging.getLogger(__name__)

SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
ARTICLE_API = "https://api.bilibili.com/x/article/view"


def generate_buvid3() -> str:
    """生成标识"""
    uid = str(uuid.uuid4()).upper()
    return f"{uid}infoc"


class BilibiliClient:
    """Bilibili 访问管理"""

    def __init__(self) -> None:
        """准备访问状态"""
        self._buvid3: Optional[str] = None

    def _get_buvid3(self) -> str:
        """获取或生成标识"""
        if not self._buvid3:
            self._buvid3 = generate_buvid3()
        return self._buvid3

    def get_headers(self) -> dict:
        """生成请求信息"""
        buvid3 = self._get_buvid3()
        cookies = [f"buvid3={buvid3}"]

        if settings.BILIBILI_SESSDATA:
            cookies.append(f"SESSDATA={settings.BILIBILI_SESSDATA}")

        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://search.bilibili.com/",
            "Origin": "https://search.bilibili.com",
            "Cookie": "; ".join(cookies),
        }

    def fetch_search(
        self, keyword: str, page: int, page_size: int, order: str
    ) -> List[Dict[str, Any]]:
        """获取搜索结果"""
        client = get_no_proxy_sync_client()
        params = {
            "search_type": "article",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "order": order,
        }

        response = client.get(
            SEARCH_API, params=params, headers=self.get_headers(), timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            logger.warning("Bilibili API error: %s", data.get("message"))
            return []

        result_data = data.get("data", {})
        return result_data.get("result", []) or []

    def fetch_article(self, article_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """获取文章内容"""
        client = get_no_proxy_sync_client()
        params = {"id": article_id}

        response = client.get(
            ARTICLE_API, params=params, headers=self.get_headers(), timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            message = data.get("message") or ""
            logger.warning("Bilibili article error: %s", message)
            return None, message

        article_data = data.get("data", {})
        return (article_data or None), ""
