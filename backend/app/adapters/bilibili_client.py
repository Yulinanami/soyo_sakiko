"""Bilibili 访问支持"""

import logging
import time
import uuid
from typing import Optional, List, Dict, Any, Tuple
from app.config import settings
from app.services.http_client import get_no_proxy_sync_client

logger = logging.getLogger(__name__)

# 需要自动重试的错误码
RETRYABLE_CODES = {-352, -401, -412}

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

    def _regenerate_buvid3(self) -> None:
        """重新生成标识（用于重试）"""
        self._buvid3 = generate_buvid3()
        logger.info("Regenerated buvid3 for retry")

    def fetch_article(
        self, article_id: str, max_retries: int = 5
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """获取文章内容（带自动重试）"""
        client = get_no_proxy_sync_client()
        params = {"id": article_id}

        last_error_code = 0
        last_message = ""

        for attempt in range(max_retries + 1):
            try:
                response = client.get(
                    ARTICLE_API, params=params, headers=self.get_headers(), timeout=15
                )
                response.raise_for_status()
                data = response.json()

                error_code = data.get("code", 0)
                if error_code == 0:
                    article_data = data.get("data", {})
                    if attempt > 0:
                        logger.info(
                            "Bilibili article %s succeeded after %d retries",
                            article_id,
                            attempt,
                        )
                    return (article_data or None), ""

                last_error_code = error_code
                last_message = data.get("message") or str(error_code)

                # 检查是否为可重试的错误码
                if error_code in RETRYABLE_CODES and attempt < max_retries:
                    delay = 0.5 * (2**attempt)  # 指数退避: 0.5s, 1s, 2s
                    logger.warning(
                        "Bilibili article %s got code %d, retrying in %.1fs (attempt %d/%d)",
                        article_id,
                        error_code,
                        delay,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(delay)
                    self._regenerate_buvid3()  # 重新生成标识
                    continue

                # 不可重试的错误或已用尽重试次数
                logger.warning(
                    "Bilibili article error for %s: code=%d, message=%s",
                    article_id,
                    error_code,
                    last_message,
                )
                return None, last_message

            except Exception as e:
                last_message = str(e)
                if attempt < max_retries:
                    delay = 0.5 * (2**attempt)
                    logger.warning(
                        "Bilibili article %s request failed, retrying in %.1fs: %s",
                        article_id,
                        delay,
                        e,
                    )
                    time.sleep(delay)
                    self._regenerate_buvid3()
                    continue
                logger.exception("Bilibili article fetch failed after retries")
                return None, last_message

        return None, last_message or "获取失败"
