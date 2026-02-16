"""Lofter 适配器"""

import logging
import time
from typing import List, Optional
from app.adapters.base import BaseAdapter
from app.adapters.lofter_content import fetch_post_content
from app.adapters.lofter_dynamic import search_dynamic_sync
from app.adapters.lofter_common import merge_novel_list
from app.schemas.novel import Novel
from app.config import settings

logger = logging.getLogger(__name__)


class LofterAdapter(BaseAdapter):
    """Lofter 来源处理"""

    source_name = "lofter"
    _dynamic_cache = {}
    _dynamic_cache_ttl_seconds = 600  # 从300秒增加到600秒（10分钟）

    def _get_cookie(self) -> Optional[str]:
        """获取 Lofter 登录信息"""
        return settings.LOFTER_COOKIE if settings.LOFTER_COOKIE else None

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """获取 Lofter 搜索结果"""
        cookie = self._get_cookie()
        if not cookie:
            logger.warning("Lofter: no cookie configured, skipping")
            return []

        exclude_tags = exclude_tags or []

        max_page_size = (
            settings.LOFTER_MAX_PAGE_SIZE or settings.LOFTER_DYNAMIC_MAX_ITEMS
        )
        if max_page_size and page_size > max_page_size:
            page_size = max_page_size

        user_tags = list(dict.fromkeys(tags))
        if not user_tags:
            return []  # 没有标签则返回空结果

        primary_tag = user_tags[0]  # 直接使用第一个标签

        ranking_type = {
            "date": "new",
            "kudos": "total",
            "hits": "total",
            "wordCount": "new",
        }.get(sort_by, "new")

        offset = (page - 1) * page_size

        if not settings.LOFTER_DYNAMIC_ENABLED:
            logger.warning("Lofter: dynamic crawling disabled, skipping")
            return []

        cache_key = self._dynamic_cache_key(primary_tag, ranking_type, exclude_tags)
        cache_entry = self._get_dynamic_cache(cache_key)
        cached_items = cache_entry["items"] if cache_entry else []
        if cache_entry and len(cached_items) >= offset + page_size:
            return cached_items[offset : offset + page_size]

        target_total = max(offset + page_size, len(cached_items) + page_size)
        ordered = await self.run_in_executor(
            search_dynamic_sync,
            primary_tag,
            ranking_type,
            page_size,
            offset,
            exclude_tags,
            cookie,
            target_total,
            True,
        )

        merged = list(cached_items) if cached_items else []
        index_map = merge_novel_list(merged, ordered)

        self._set_dynamic_cache(cache_key, merged, False)

        if offset >= len(merged):
            return []
        novels = merged[offset : offset + page_size]
        return novels

    def _dynamic_cache_key(
        self, tag: str, ranking_type: str, exclude_tags: List[str]
    ) -> str:
        """生成保存用标识"""
        exclude_key = ",".join(sorted(exclude_tags)) if exclude_tags else ""
        return f"{tag}:{ranking_type}:{exclude_key}"

    def _get_dynamic_cache(self, key: str):
        """读取已存内容"""
        entry = self._dynamic_cache.get(key)
        if not entry:
            return None
        ttl = settings.LOFTER_DYNAMIC_CACHE_TTL or self._dynamic_cache_ttl_seconds
        if time.time() - entry["timestamp"] > ttl:
            self._dynamic_cache.pop(key, None)
            return None
        return entry

    def _set_dynamic_cache(self, key: str, items: List[Novel], exhausted: bool) -> None:
        """写入已存内容"""
        if key not in self._dynamic_cache and len(self._dynamic_cache) >= 20:
            oldest = min(
                self._dynamic_cache, key=lambda k: self._dynamic_cache[k]["timestamp"]
            )
            del self._dynamic_cache[oldest]
        self._dynamic_cache[key] = {
            "items": items,
            "timestamp": time.time(),
            "exhausted": exhausted,
        }

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """返回 Lofter 详情结果"""
        return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 Lofter 章节列表"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """获取 Lofter 章节内容"""
        cookie = self._get_cookie()
        if not cookie:
            return "<p>请配置 LOFTER_COOKIE 后重试</p>"

        try:
            content = await self.run_in_executor(fetch_post_content, novel_id, cookie)
            return content
        except Exception as e:
            logger.exception("Lofter content fetch error")
            return f"<p>获取内容失败: {e}</p>"
