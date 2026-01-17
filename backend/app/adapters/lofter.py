"""
Lofter Adapter
Uses DWR (Direct Web Remoting) API to search for novels by tag
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from app.adapters.base import BaseAdapter
from app.adapters.lofter_content import fetch_post_content
from app.adapters.lofter_dynamic import search_dynamic_sync
from app.adapters.lofter_common import merge_novel_fields
from app.adapters.utils import novel_key
from app.schemas.novel import Novel, NovelSource
from app.config import settings


class LofterAdapter(BaseAdapter):
    """Adapter for Lofter platform"""

    source_name = "lofter"
    _executor = ThreadPoolExecutor(max_workers=2)

    # SoyoSaki related tags on Lofter
    SOYOSAKI_TAGS = ["素祥", "祥素", "そよさき"]
    _dynamic_cache = {}
    _dynamic_cache_ttl_seconds = 300

    def _get_cookie(self) -> Optional[str]:
        """Get Lofter cookie from settings"""
        return settings.LOFTER_COOKIE if settings.LOFTER_COOKIE else None

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """Search for novels by tags on Lofter"""
        cookie = self._get_cookie()
        if not cookie:
            print("⚠️ Lofter: No cookie configured, skipping")
            return []

        exclude_tags = exclude_tags or []

        max_page_size = settings.LOFTER_MAX_PAGE_SIZE or settings.LOFTER_DYNAMIC_MAX_ITEMS
        if max_page_size and page_size > max_page_size:
            page_size = max_page_size

        user_tags = list(dict.fromkeys(tags))
        if not user_tags:
            user_tags = list(self.SOYOSAKI_TAGS)
        if not user_tags:
            user_tags = ["素祥"]

        # Prefer a non-default tag if user selected one
        primary_tag = next(
            (tag for tag in user_tags if tag not in self.SOYOSAKI_TAGS),
            user_tags[0],
        )

        # Map sort_by to Lofter's ranking type
        ranking_type = {
            "date": "new",
            "kudos": "total",
            "hits": "total",
            "wordCount": "new",
        }.get(sort_by, "new")

        # Calculate offset
        offset = (page - 1) * page_size

        if not settings.LOFTER_DYNAMIC_ENABLED:
            print("⚠️ Lofter: dynamic crawling disabled, skipping")
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
        index_map = {
            novel_key(n.source, n.id): idx for idx, n in enumerate(merged)
        }
        for novel in ordered:
            key = novel_key(novel.source, novel.id)
            idx = index_map.get(key)
            if idx is None:
                index_map[key] = len(merged)
                merged.append(novel)
            else:
                merge_novel_fields(merged[idx], novel)

        self._set_dynamic_cache(cache_key, merged, False)

        if offset >= len(merged):
            return []
        novels = merged[offset : offset + page_size]

        if len(novels) > page_size:
            novels = novels[:page_size]

        return novels

    def _dynamic_cache_key(
        self, tag: str, ranking_type: str, exclude_tags: List[str]
    ) -> str:
        exclude_key = ",".join(sorted(exclude_tags)) if exclude_tags else ""
        return f"{tag}:{ranking_type}:{exclude_key}"

    def _get_dynamic_cache(self, key: str):
        entry = self._dynamic_cache.get(key)
        if not entry:
            return None
        ttl = settings.LOFTER_DYNAMIC_CACHE_TTL or self._dynamic_cache_ttl_seconds
        if time.time() - entry["timestamp"] > ttl:
            self._dynamic_cache.pop(key, None)
            return None
        return entry

    def _set_dynamic_cache(self, key: str, items: List[Novel], exhausted: bool) -> None:
        self._dynamic_cache[key] = {
            "items": items,
            "timestamp": time.time(),
            "exhausted": exhausted,
        }

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """Get novel details - for Lofter we redirect to source URL"""
        # Lofter posts don't have a detail API, we use the source_url directly
        # Return None to indicate detail should be fetched fresh
        return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """Get chapter list - Lofter posts are typically single chapter"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """Get chapter content by fetching the blog post page"""
        cookie = self._get_cookie()
        if not cookie:
            return "<p>请配置 LOFTER_COOKIE 后重试</p>"

        # novel_id format: postId (e.g., "4cefde3_2hdf80424") or blogName_timestamp
        # We need to construct the post URL
        try:
            content = await self.run_in_executor(fetch_post_content, novel_id, cookie)
            return content
        except Exception as e:
            print(f"Lofter content fetch error: {e}")
            return f"<p>获取内容失败: {e}</p>"
