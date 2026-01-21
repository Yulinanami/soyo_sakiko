"""AO3 来源处理"""

import logging
from typing import List, Optional
from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, exclude_any_tag, to_iso_date, with_retries
from app.schemas.novel import Novel, NovelSource

logger = logging.getLogger(__name__)

try:
    import AO3

    AO3_AVAILABLE = True
except ImportError:
    AO3_AVAILABLE = False
    logger.warning("AO3 library not installed. Run: pip install ao3-api")


class AO3Adapter(BaseAdapter):
    """AO3 来源处理"""

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
        if not AO3_AVAILABLE:
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
            tag_query = " OR ".join(f'"{tag}"' for tag in tags)

            search = AO3.Search(
                any_field=tag_query,
                sort_column=self._map_sort(sort_by),
                sort_direction="desc",
            )

            def _update() -> None:
                """刷新搜索结果"""
                search.update()

            try:
                with_retries(
                    _update,
                    retries=2,
                    base_delay=0.8,
                    max_delay=2.0,
                    on_retry=lambda exc, attempt: logger.warning(
                        "AO3 search retry %s after error: %s", attempt, exc
                    ),
                )
            except Exception as e:
                logger.warning("AO3 search update failed: %s", e)
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

                    novel = self._convert_work(work)
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

    def _map_sort(self, sort_by: str) -> str:
        """映射排序字段"""
        mapping = {
            "date": "revised_at",
            "kudos": "kudos_count",
            "hits": "hits",
            "wordCount": "word_count",
        }
        return mapping.get(sort_by, "revised_at")

    def _convert_work(self, work) -> Novel:
        """转换 AO3 条目为小说结构"""
        author = "Anonymous"
        author_url = None
        if work.authors:
            author = work.authors[0].username
            author_url = f"https://archiveofourown.org/users/{author}"

        tags = []
        try:
            if hasattr(work, "tags"):
                tags = [str(tag) for tag in work.tags[:20]]
        except:
            pass

        published_at = to_iso_date(getattr(work, "date_published", None))
        updated_at = to_iso_date(getattr(work, "date_updated", None))
        if not published_at:
            published_at = updated_at

        summary = ""
        try:
            summary = work.summary or ""
        except Exception:
            summary = ""

        return Novel(
            id=str(work.id),
            source=NovelSource.AO3,
            title=work.title or "Untitled",
            author=author,
            author_url=author_url,
            summary=summary,
            tags=tags,
            rating=getattr(work, "rating", None),
            word_count=getattr(work, "words", None),
            chapter_count=getattr(work, "nchapters", 1),
            kudos=getattr(work, "kudos", 0),
            hits=getattr(work, "hits", 0),
            published_at=published_at,
            updated_at=updated_at,
            source_url=work.url,
            is_complete=getattr(work, "complete", None),
        )

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情"""
        if not AO3_AVAILABLE:
            return None

        return await self.run_in_executor(self._get_detail_sync, novel_id)

    def _get_detail_sync(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情"""
        try:
            work = with_retries(
                lambda: AO3.Work(int(novel_id)),
                retries=2,
                base_delay=0.6,
                max_delay=2.0,
                on_retry=lambda exc, attempt: logger.warning(
                    "AO3 detail retry %s for %s after error: %s",
                    attempt,
                    novel_id,
                    exc,
                ),
            )
            return self._convert_work(work)
        except Exception:
            logger.exception("AO3 detail fetch failed for %s", novel_id)
            return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        if not AO3_AVAILABLE:
            return []

        return await self.run_in_executor(self._get_chapters_sync, novel_id)

    def _get_chapters_sync(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        try:
            work = with_retries(
                lambda: AO3.Work(int(novel_id)),
                retries=2,
                base_delay=0.6,
                max_delay=2.0,
                on_retry=lambda exc, attempt: logger.warning(
                    "AO3 chapters retry %s for %s after error: %s",
                    attempt,
                    novel_id,
                    exc,
                ),
            )
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
        if not AO3_AVAILABLE:
            return None

        return await self.run_in_executor(
            self._get_chapter_content_sync, novel_id, chapter_num
        )

    def _get_chapter_content_sync(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取 AO3 章节内容"""
        try:
            work = with_retries(
                lambda: AO3.Work(int(novel_id)),
                retries=2,
                base_delay=0.6,
                max_delay=2.0,
                on_retry=lambda exc, attempt: logger.warning(
                    "AO3 content retry %s for %s after error: %s",
                    attempt,
                    novel_id,
                    exc,
                ),
            )
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
