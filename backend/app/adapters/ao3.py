"""AO3 处理入口"""

import logging
from typing import List, Optional
from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, exclude_any_tag
from app.adapters.ao3_client import build_search, get_work, is_available, update_search
from app.adapters.ao3_parse import map_sort, work_to_novel
from app.schemas.novel import Novel

logger = logging.getLogger(__name__)


class AO3Adapter(BaseAdapter):
    """处理 AO3 数据"""

    source_name = "ao3"

    SOYOSAKI_TAGS = [
        "Nagasaki Soyo/Toyokawa Sakiko",
        "Toyokawa Sakiko/Nagasaki Soyo",
    ]

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """获取 AO3 搜索结果"""
        if not is_available():
            logger.warning("AO3 library not available")
            return []

        exclude_tags = exclude_tags or []

        search_tags = list(set(tags + self.SOYOSAKI_TAGS))

        return await self.run_in_executor(
            self._search_sync,
            search_tags,
            exclude_tags,
            page,
            page_size,
            sort_by,
        )

    def _search_sync(
        self,
        tags: List[str],
        exclude_tags: List[str],
        page: int,
        page_size: int,
        sort_by: str,
    ) -> List[Novel]:
        """获取 AO3 搜索结果"""
        try:
            search = build_search(tags, map_sort(sort_by))
            if not update_search(search):
                return []

            novels = []
            start = (page - 1) * page_size
            end = start + page_size * 2

            for work in search.results[start:end]:
                if len(novels) >= page_size:
                    break
                try:
                    title = getattr(work, "title", "") or ""
                    if exclude(title, exclude_tags):
                        continue

                    novel = work_to_novel(work)
                    if exclude_any_tag(novel.tags, exclude_tags):
                        continue
                    novels.append(novel)
                except Exception:
                    logger.warning("AO3 work conversion failed")
                    continue

            return novels
        except Exception as e:
            logger.warning("AO3 search error: %s", e)
            return []

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情"""
        if not is_available():
            return None

        return await self.run_in_executor(self._get_detail_sync, novel_id)

    def _get_detail_sync(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情"""
        try:
            work = get_work(novel_id)
            return work_to_novel(work)
        except Exception:
            logger.exception("AO3 detail fetch failed for %s", novel_id)
            return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        if not is_available():
            return []

        return await self.run_in_executor(self._get_chapters_sync, novel_id)

    def _get_chapters_sync(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        try:
            work = get_work(novel_id)
            chapters = []
            for i, chapter in enumerate(work.chapters, 1):
                chapters.append({"number": i, "title": chapter.title or f"Chapter {i}"})
            return chapters
        except Exception:
            logger.exception("AO3 chapters fetch failed for %s", novel_id)
            return []

    async def get_chapter_content(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取 AO3 章节内容"""
        if not is_available():
            return None

        return await self.run_in_executor(
            self._get_chapter_content_sync, novel_id, chapter_num
        )

    def _get_chapter_content_sync(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取 AO3 章节内容"""
        try:
            work = get_work(novel_id)
            if chapter_num <= len(work.chapters):
                chapter = work.chapters[chapter_num - 1]
                return chapter.text
            return None
        except Exception:
            logger.exception(
                "AO3 chapter content fetch failed for %s (chapter %s)",
                novel_id,
                chapter_num,
            )
            return None
