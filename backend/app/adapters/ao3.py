"""AO3 处理入口"""

import logging
from typing import List, Optional
from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, exclude_any_tag
from app.adapters.ao3_dynamic import get_work_details_dynamic_sync, search_dynamic_sync
from app.adapters.ao3_parse import (
    map_sort,
    parse_search_results_html,
    parse_work_detail_html,
)
from app.schemas.novel import Novel

logger = logging.getLogger(__name__)


class AO3Adapter(BaseAdapter):
    """处理 AO3 数据"""

    source_name = "ao3"

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """获取 AO3 搜索结果"""
        exclude_tags = exclude_tags or []

        return await self.run_in_executor(
            self._search_sync,
            tags,
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
        """获取 AO3 搜索结果 (动态爬虫深度版本)"""
        try:
            novels = []
            # AO3 每页 20 条。我们要找 page_size (通常 30) 条。
            # 根据请求的 page 计算 AO3 的起始页
            current_ao3_page = ((page - 1) * page_size // 20) + 1
            max_ao3_pages = 3  # 每次请求最多查 3 页 AO3 深度
            pages_searched = 0

            while len(novels) < page_size and pages_searched < max_ao3_pages:
                # 1. 抓取 HTML
                html = search_dynamic_sync(tags, map_sort(sort_by), current_ao3_page)
                if not html or html == "EMPTY":
                    break

                # 2. 解析 HTML
                results = parse_search_results_html(html)
                if not results:
                    break

                # 3. 过滤并追加
                for novel in results:
                    # 严格包含检测 (忽略大小写)
                    tags_lower = [t.lower() for t in tags]
                    has_tag = any(
                        any(tl in tag.lower() for tag in novel.tags)
                        for tl in tags_lower
                    )
                    has_title_summary = any(
                        tl in (novel.title or "").lower() for tl in tags_lower
                    ) or any(tl in (novel.summary or "").lower() for tl in tags_lower)

                    if not has_tag and not has_title_summary:
                        continue

                    # 排除检测
                    if (
                        exclude_any_tag(novel.tags, exclude_tags)
                        or exclude(novel.title, exclude_tags)
                        or exclude(novel.summary, exclude_tags)
                    ):
                        continue

                    # 查重
                    if not any(n.id == novel.id for n in novels):
                        novels.append(novel)
                        if len(novels) >= page_size:
                            break

                current_ao3_page += 1
                pages_searched += 1

            return novels
        except Exception as e:
            logger.warning(f"AO3: Search error: {e}")
            return []

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情 (动态版)"""
        return await self.run_in_executor(self._get_detail_sync, novel_id)

    def _get_detail_sync(self, novel_id: str) -> Optional[Novel]:
        """获取 AO3 详情 (动态版)"""
        try:
            data = get_work_details_dynamic_sync(novel_id)
            if not data or not data.get("html"):
                return None

            return parse_work_detail_html(data["html"], novel_id)
        except Exception:
            return Novel(
                id=novel_id,
                source="ao3",
                title="Loading...",
                author="Unknown",
                summary="",
                tags=[],
                published_at="",
                source_url=f"https://archiveofourown.org/works/{novel_id}",
            )

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        return await self.run_in_executor(self._get_chapters_sync, novel_id)

    def _get_chapters_sync(self, novel_id: str) -> List[dict]:
        """获取 AO3 章节列表"""
        try:
            data = get_work_details_dynamic_sync(novel_id)
            return data.get("chapters", [])
        except Exception:
            return []

    async def get_chapter_content(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取 AO3 章节内容"""
        return await self.run_in_executor(
            self._get_chapter_content_sync, novel_id, chapter_num
        )

    def _get_chapter_content_sync(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取 AO3 章节内容"""
        try:
            data = get_work_details_dynamic_sync(novel_id, chapter_num)
            return data.get("chapter_content")
        except Exception:
            return None
