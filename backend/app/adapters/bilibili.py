"""Bilibili 处理入口"""

import asyncio
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
        exclude_tags = [t.strip() for t in (exclude_tags or []) if t.strip()]
        user_tags = [t.strip() for t in (tags or []) if t.strip()]
        if not user_tags:
            return []
        keyword = user_tags[0]

        order_map = {
            "date": "pubdate",
            "kudos": "totalrank",
            "hits": "click",
            "wordCount": "pubdate",
        }
        order = order_map.get(sort_by, "pubdate")

        try:
            # 异步搜索
            articles = await self._client.fetch_search_async(
                keyword, page, page_size, order
            )

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

            # 1. 基础过滤
            if novels:
                novels = [
                    n
                    for n in novels
                    if (
                        any(any(t in tag for tag in n.tags) for t in user_tags)
                        or any(t in n.title for t in user_tags)
                        or any(t in n.summary for t in user_tags)
                    )
                    and not exclude(n.title, exclude_tags)
                    and not exclude(n.summary, exclude_tags)
                    and not exclude_any_tag(n.tags, exclude_tags)
                ]

            # 2. 并发获取详情进行增强过滤
            if novels:
                semaphore = asyncio.Semaphore(3)

                async def check_and_filter(novel: Novel, index: int) -> Optional[Novel]:
                    """检查并过滤单条结果"""
                    async with semaphore:
                        try:
                            if index > 0:
                                await asyncio.sleep(0.3)

                            detail = await self.get_detail(novel.id)
                            if detail:
                                has_tag = any(
                                    any(t in tag for tag in detail.tags)
                                    for t in user_tags
                                )
                                has_title_summary = any(
                                    t in detail.title for t in user_tags
                                ) or any(t in detail.summary for t in user_tags)

                                if not has_tag and not has_title_summary:
                                    logger.info(
                                        f"Filtered out Bilibili article {novel.id} due to inclusion mismatch"
                                    )
                                    return None

                                if exclude_any_tag(detail.tags, exclude_tags):
                                    logger.info(
                                        f"Filtered out Bilibili article {novel.id} due to tag match in detail: {detail.tags}"
                                    )
                                    return None

                                if exclude(detail.title, exclude_tags) or exclude(
                                    detail.summary, exclude_tags
                                ):
                                    logger.info(
                                        f"Filtered out Bilibili article {novel.id} due to title/summary match in detail"
                                    )
                                    return None

                                novel.tags = detail.tags
                                novel.title = detail.title
                                novel.summary = detail.summary
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

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取 Bilibili 详情（原生 async）"""
        try:
            article_data, _message = await self._client.fetch_article_async(novel_id)
            if not article_data:
                return None
            return parse_article_detail(article_data, novel_id)
        except Exception:
            logger.exception("Bilibili get_detail error for %s", novel_id)
            return None

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取 Bilibili 章节列表"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """获取 Bilibili 内容（原生 async）"""
        try:
            article_data, message = await self._client.fetch_article_async(novel_id)
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
        except Exception:
            logger.exception("Bilibili get_chapter_content error for %s", novel_id)
            return "<p>获取内容失败</p>"
