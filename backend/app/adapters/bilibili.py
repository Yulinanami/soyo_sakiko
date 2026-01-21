"""Bilibili 处理入口"""

import logging
from typing import List, Optional

from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, exclude_any_tag
from app.schemas.novel import Novel
from app.adapters.bilibili_client import BilibiliClient
from app.adapters.bilibili_parse import (
    parse_article_summary,
    parse_article_detail,
    parse_opus_content,
    parse_bilibili_content,
    rewrite_image_urls,
)

logger = logging.getLogger(__name__)

class BilibiliAdapter(BaseAdapter):
    """处理 Bilibili 数据"""

    source_name = "bilibili"
    SOYOSAKI_TAGS = ["素祥", "祥素", "长崎素世", "丰川祥子"]
    def __init__(self) -> None:
        """初始化所需状态"""
        super().__init__()
        self._client = BilibiliClient()

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """获取 Bilibili 搜索结果"""
        exclude_tags = exclude_tags or []

        user_tags = list(dict.fromkeys(tags))
        if not user_tags:
            user_tags = list(self.SOYOSAKI_TAGS)
        keyword = user_tags[0] if user_tags else "素祥"

        order_map = {
            "date": "pubdate",
            "kudos": "totalrank",
            "hits": "click",
            "wordCount": "pubdate",
        }
        order = order_map.get(sort_by, "pubdate")

        try:
            novels = await self.run_in_executor(
                self._search_sync, keyword, page, page_size, order
            )

            if exclude_tags and novels:
                novels = [
                    n
                    for n in novels
                    if not exclude(n.title, exclude_tags)
                    and not exclude(n.summary, exclude_tags)
                ]

            if exclude_tags and novels:
                import asyncio

                semaphore = asyncio.Semaphore(3)

                async def check_and_filter(novel: Novel, index: int) -> Optional[Novel]:
                    """检查并过滤单条结果"""
                    async with semaphore:
                        try:
                            if index > 0:
                                await asyncio.sleep(0.3)

                            detail = await self.get_detail(novel.id)
                            if detail and detail.tags:
                                if exclude_any_tag(detail.tags, exclude_tags):
                                    logger.info(
                                        f"Filtered out article {novel.id} due to tag match"
                                    )
                                    return None
                                novel.tags = detail.tags
                            return novel
                        except Exception as e:
                            logger.warning(f"Error fetching detail for {novel.id}: {e}")
                            return novel

                results = await asyncio.gather(
                    *[check_and_filter(n, i) for i, n in enumerate(novels)],
                    return_exceptions=True,
                )
                novels = [
                    r for r in results if r is not None and not isinstance(r, Exception)
                ]
                logger.info(f"After enhanced filter: {len(novels)} novels remaining")

            return novels
        except Exception:
            logger.exception("Bilibili search error")
            return []

    def _search_sync(
        self, keyword: str, page: int, page_size: int, order: str
    ) -> List[Novel]:
        """获取 Bilibili 搜索结果"""
        articles = self._client.fetch_search(keyword, page, page_size, order)

        if not articles:
            return []

        novels = []
        for article in articles:
            try:
                novel = parse_article_summary(article)
                if novel:
                    novels.append(novel)
            except Exception:
                logger.exception(
                    "Error parsing Bilibili article: %s", article.get("id")
                )
                continue

        logger.info(
            "Bilibili fetched %d articles for keyword '%s'", len(novels), keyword
        )
        return novels

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取 Bilibili 详情"""
        try:
            return await self.run_in_executor(self._get_detail_sync, novel_id)
        except Exception:
            logger.exception("Bilibili get_detail error for %s", novel_id)
            return None

    def _get_detail_sync(self, novel_id: str) -> Optional[Novel]:
        """获取 Bilibili 详情"""
        article_data, _message = self._client.fetch_article(novel_id)
        if not article_data:
            return None
        return parse_article_detail(article_data, novel_id)

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 Bilibili 章节列表"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """获取 Bilibili 内容"""
        try:
            return await self.run_in_executor(self._get_content_sync, novel_id)
        except Exception:
            logger.exception("Bilibili get_chapter_content error for %s", novel_id)
            return "<p>获取内容失败</p>"

    def _get_content_sync(self, novel_id: str) -> Optional[str]:
        """获取 Bilibili 内容"""
        article_data, message = self._client.fetch_article(novel_id)
        if not article_data:
            if message:
                return f"<p>获取失败: {message}</p>"
            return "<p>获取内容失败</p>"

        opus_data = article_data.get("opus", {})
        if opus_data:
            content = parse_opus_content(opus_data)
            logger.info(
                f"Opus content parsed, length: {len(content)}, has img: {'<img' in content}"
            )
            if content:
                content = rewrite_image_urls(content)
                logger.info(f"After rewrite, has proxy: {'/api/proxy/' in content}")
                return f'<div class="bilibili-article">{content}</div>'

        content = article_data.get("content", "")

        if not content:
            read_info = article_data.get("readInfo", {})
            content = read_info.get("content", "")

        if not content:
            return "<p>文章内容为空</p>"

        content = parse_bilibili_content(content)
        content = rewrite_image_urls(content)
        return f'<div class="bilibili-article">{content}</div>'
