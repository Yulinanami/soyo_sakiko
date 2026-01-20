"""
Bilibili Adapter
Fetches articles (专栏) from Bilibili using unofficial API
"""

import logging
import re
import uuid
from typing import List, Optional
from datetime import datetime

from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, exclude_any_tag
from app.schemas.novel import Novel, NovelSource
from app.config import settings
from app.services.http_client import get_sync_client

logger = logging.getLogger(__name__)

# Bilibili API endpoints
SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
ARTICLE_API = "https://api.bilibili.com/x/article/view"


def _generate_buvid3() -> str:
    """Generate a pseudo-random buvid3 cookie value"""
    # buvid3 format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXXinfoc
    uid = str(uuid.uuid4()).upper()
    return f"{uid}infoc"


class BilibiliAdapter(BaseAdapter):
    """Adapter for Bilibili articles (专栏)"""

    source_name = "bilibili"
    SOYOSAKI_TAGS = ["素祥", "祥素", "长崎素世", "丰川祥子"]
    _buvid3: Optional[str] = None

    def _get_buvid3(self) -> str:
        """Get or generate buvid3 cookie"""
        if not self._buvid3:
            self._buvid3 = _generate_buvid3()
        return self._buvid3

    def _get_headers(self) -> dict:
        """Get request headers with anti-bot cookies"""
        buvid3 = self._get_buvid3()
        cookies = [f"buvid3={buvid3}"]

        if settings.BILIBILI_SESSDATA:
            cookies.append(f"SESSDATA={settings.BILIBILI_SESSDATA}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://search.bilibili.com/",
            "Origin": "https://search.bilibili.com",
            "Cookie": "; ".join(cookies),
        }
        return headers

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """Search for articles by tags on Bilibili"""
        exclude_tags = exclude_tags or []

        # Use the first tag as keyword
        user_tags = list(dict.fromkeys(tags))
        if not user_tags:
            user_tags = list(self.SOYOSAKI_TAGS)
        keyword = user_tags[0] if user_tags else "素祥"

        # Map sort_by to Bilibili order
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

            # Apply basic exclude filter first (title/summary)
            if exclude_tags and novels:
                novels = [
                    n
                    for n in novels
                    if not exclude(n.title, exclude_tags)
                    and not exclude(n.summary, exclude_tags)
                ]

            # Enhanced filtering: fetch details to get real tags
            if exclude_tags and novels:
                import asyncio

                # Limit concurrent requests to avoid rate limiting
                semaphore = asyncio.Semaphore(3)

                async def check_and_filter(novel: Novel, index: int) -> Optional[Novel]:
                    async with semaphore:
                        try:
                            # Add small delay between requests
                            if index > 0:
                                await asyncio.sleep(0.3)

                            # Fetch detail to get real tags
                            detail = await self.get_detail(novel.id)
                            if detail and detail.tags:
                                # Check if any real tag matches exclude patterns
                                if exclude_any_tag(detail.tags, exclude_tags):
                                    logger.info(
                                        f"Filtered out article {novel.id} due to tag match"
                                    )
                                    return None
                                # Update novel with real tags
                                novel.tags = detail.tags
                            return novel
                        except Exception as e:
                            logger.warning(f"Error fetching detail for {novel.id}: {e}")
                            return novel  # Keep on error

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
        """Synchronous search implementation"""
        client = get_sync_client()
        params = {
            "search_type": "article",
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "order": order,
        }

        response = client.get(
            SEARCH_API, params=params, headers=self._get_headers(), timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            logger.warning("Bilibili API error: %s", data.get("message"))
            return []

        result_data = data.get("data", {})
        articles = result_data.get("result", [])

        if not articles:
            return []

        novels = []
        for article in articles:
            try:
                novel = self._parse_article(article)
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

    def _parse_article(self, article: dict) -> Optional[Novel]:
        """Parse Bilibili article data into Novel schema"""
        article_id = str(article.get("id", ""))
        if not article_id:
            return None

        title = article.get("title", "")
        # Remove HTML tags from title
        title = re.sub(r"<[^>]+>", "", title)

        # Get author - search API doesn't include uname, use mid as display
        mid = article.get("mid", "")
        author = article.get("uname", "") or article.get("author", "")
        if not author and mid:
            author = f"uid:{mid}"  # Show uid directly
        author_url = f"https://space.bilibili.com/{mid}" if mid else None

        # Get description/summary
        summary = article.get("desc", "") or article.get("description", "")
        summary = re.sub(r"<[^>]+>", "", summary)

        # Get tags from category info
        tags = []
        category_name = article.get("category_name", "")
        if category_name:
            tags.append(category_name)

        # Stats
        view = article.get("view", 0)
        like = article.get("like", 0)

        # Timestamps
        pub_time = article.get("pub_time", 0)
        if pub_time:
            published_at = datetime.fromtimestamp(pub_time).isoformat()
        else:
            published_at = datetime.now().isoformat()

        # Cover image - fix URL prefix
        cover = article.get("image_urls", [])
        cover_image = cover[0] if cover else None
        if not cover_image:
            origin_urls = article.get("origin_image_urls", [])
            cover_image = origin_urls[0] if origin_urls else None

        # Add https: prefix if URL starts with //
        if cover_image and cover_image.startswith("//"):
            cover_image = "https:" + cover_image

        # Word count (approximate from template info)
        word_count = article.get("words", 0)

        return Novel(
            id=article_id,
            source=NovelSource.BILIBILI,
            title=title,
            author=author,
            author_url=author_url,
            summary=summary,
            tags=tags,
            rating=None,
            word_count=word_count if word_count else None,
            chapter_count=1,
            kudos=like,
            hits=view,
            published_at=published_at,
            updated_at=None,
            source_url=f"https://www.bilibili.com/read/cv{article_id}",
            cover_image=cover_image,
            is_complete=True,
        )

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """Get article details"""
        try:
            return await self.run_in_executor(self._get_detail_sync, novel_id)
        except Exception:
            logger.exception("Bilibili get_detail error for %s", novel_id)
            return None

    def _get_detail_sync(self, novel_id: str) -> Optional[Novel]:
        """Synchronous get detail implementation"""
        client = get_sync_client()
        params = {"id": novel_id}

        response = client.get(
            ARTICLE_API, params=params, headers=self._get_headers(), timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            logger.warning("Bilibili article API error: %s", data.get("message"))
            return None

        article_data = data.get("data", {})
        if not article_data:
            return None

        # Parse article detail
        article_id = str(article_data.get("id", novel_id))
        title = article_data.get("title", "")
        author_info = article_data.get("author", {})
        author = author_info.get("name", "")
        mid = author_info.get("mid", "")
        author_url = f"https://space.bilibili.com/{mid}" if mid else None

        summary = article_data.get("summary", "")

        # Tags - get from both categories and actual tags field
        tags = []
        categories = article_data.get("categories", [])
        for cat in categories:
            if cat.get("name"):
                tags.append(cat["name"])

        # Also get actual article tags
        actual_tags = article_data.get("tags", [])
        for tag_item in actual_tags:
            tag_name = (
                tag_item.get("name", "")
                if isinstance(tag_item, dict)
                else str(tag_item)
            )
            if tag_name and tag_name not in tags:
                tags.append(tag_name)

        # Stats
        stats = article_data.get("stats", {})
        view = stats.get("view", 0)
        like = stats.get("like", 0)

        # Timestamps
        pub_time = article_data.get("publish_time", 0)
        published_at = (
            datetime.fromtimestamp(pub_time).isoformat()
            if pub_time
            else datetime.now().isoformat()
        )

        # Cover image
        cover_image = (
            article_data.get("banner_url", "")
            or article_data.get("image_urls", [""])[0]
            if article_data.get("image_urls")
            else None
        )
        # Add https: prefix if needed
        if cover_image and cover_image.startswith("//"):
            cover_image = "https:" + cover_image

        # Word count
        word_count = article_data.get("words", 0)

        # Get dynamic_id for opus URL (newer format)
        opus_data = article_data.get("opus", {})
        dynamic_id = opus_data.get("dynamic_id_str", "")

        # Use opus URL if dynamic_id exists, otherwise fallback to cv URL
        if dynamic_id:
            source_url = f"https://www.bilibili.com/opus/{dynamic_id}"
        else:
            source_url = f"https://www.bilibili.com/read/cv{article_id}"

        return Novel(
            id=article_id,
            source=NovelSource.BILIBILI,
            title=title,
            author=author,
            author_url=author_url,
            summary=summary,
            tags=tags,
            rating=None,
            word_count=word_count if word_count else None,
            chapter_count=1,
            kudos=like,
            hits=view,
            published_at=published_at,
            updated_at=None,
            source_url=source_url,
            cover_image=cover_image,
            is_complete=True,
        )

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """Get chapter list - Bilibili articles are single chapter"""
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """Get article content"""
        try:
            return await self.run_in_executor(self._get_content_sync, novel_id)
        except Exception:
            logger.exception("Bilibili get_chapter_content error for %s", novel_id)
            return "<p>获取内容失败</p>"

    def _get_content_sync(self, novel_id: str) -> Optional[str]:
        """Synchronous get content implementation"""
        client = get_sync_client()
        params = {"id": novel_id}

        response = client.get(
            ARTICLE_API, params=params, headers=self._get_headers(), timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != 0:
            return f"<p>获取失败: {data.get('message')}</p>"

        article_data = data.get("data", {})

        # Try to get content from opus rich_text_nodes first (includes images)
        opus_data = article_data.get("opus", {})
        if opus_data:
            content = self._parse_opus_content(opus_data)
            logger.info(
                f"Opus content parsed, length: {len(content)}, has img: {'<img' in content}"
            )
            if content:
                content = self._rewrite_image_urls(content)
                logger.info(f"After rewrite, has proxy: {'/api/proxy/' in content}")
                return f'<div class="bilibili-article">{content}</div>'

        # Fallback to traditional content field
        content = article_data.get("content", "")

        if not content:
            # Try to get from readInfo if available
            read_info = article_data.get("readInfo", {})
            content = read_info.get("content", "")

        if not content:
            return "<p>文章内容为空</p>"

        # Parse Bilibili JSON content format
        content = self._parse_bilibili_content(content)

        # Rewrite image URLs to use proxy
        content = self._rewrite_image_urls(content)

        # Add some basic styling wrapper
        styled_content = f'<div class="bilibili-article">{content}</div>'
        return styled_content

    def _parse_opus_content(self, opus_data: dict) -> str:
        """Parse opus rich text content with images from content.paragraphs"""
        html_parts = []

        # Get content paragraphs
        content = opus_data.get("content", {})
        paragraphs = content.get("paragraphs", [])

        for para in paragraphs:
            para_type = para.get("para_type")

            if para_type == 1:  # Text paragraph
                text_data = para.get("text", {})
                nodes = text_data.get("nodes", [])
                for node in nodes:
                    word_data = node.get("word", {})
                    words = word_data.get("words", "")
                    if words:
                        # Replace newlines with br tags
                        words = words.replace("\n", "<br>")
                        html_parts.append(f"<p>{words}</p>")

            elif para_type == 2:  # Picture paragraph
                pic_data = para.get("pic", {})
                pics = pic_data.get("pics", [])
                for pic in pics:
                    pic_url = pic.get("url", "")
                    if pic_url:
                        # Add https: prefix if needed
                        if pic_url.startswith("//"):
                            pic_url = "https:" + pic_url
                        html_parts.append(
                            f'<figure><img src="{pic_url}" alt="image" style="max-width:100%;"></figure>'
                        )

        return "".join(html_parts) if html_parts else ""

    def _rewrite_image_urls(self, content: str) -> str:
        """Rewrite Bilibili image URLs to use proxy endpoint"""
        import urllib.parse

        # Match img src attributes with hdslb.com or bilibili.com URLs
        def replace_url(match):
            url = match.group(1)
            # Handle protocol-relative URLs
            if url.startswith("//"):
                url = "https:" + url
            # Only proxy Bilibili image domains
            if "hdslb.com" in url or "bilibili.com" in url:
                proxy_url = (
                    f"/api/proxy/bilibili?url={urllib.parse.quote(url, safe='')}"
                )
                return f'src="{proxy_url}"'
            return match.group(0)

        # Replace src="..." patterns
        content = re.sub(r'src="([^"]+)"', replace_url, content)
        content = re.sub(r"src='([^']+)'", replace_url, content)

        return content

    def _parse_bilibili_content(self, content: str) -> str:
        """Parse Bilibili rich text content format"""
        import json

        # If content starts with JSON marker, try to parse it
        if content.startswith('{"ops"') or content.startswith("["):
            try:
                data = json.loads(content)
                # Handle {"ops": [...]} format
                if isinstance(data, dict) and "ops" in data:
                    ops = data["ops"]
                elif isinstance(data, list):
                    ops = data
                else:
                    return content

                # Convert ops to HTML
                html_parts = []
                for op in ops:
                    if isinstance(op, dict):
                        insert = op.get("insert", "")
                        if isinstance(insert, str):
                            # Replace newlines with paragraph breaks
                            text = insert.replace("\n\n", "</p><p>").replace(
                                "\n", "<br>"
                            )
                            html_parts.append(text)
                        elif isinstance(insert, dict):
                            # Handle embedded objects (images, etc.)
                            if "image" in insert:
                                img_url = insert["image"]
                                html_parts.append(
                                    f'<img src="{img_url}" alt="image" style="max-width:100%;">'
                                )

                content = "<p>" + "".join(html_parts) + "</p>"
                # Clean up empty paragraphs
                content = re.sub(r"<p>\s*</p>", "", content)
                content = re.sub(r"<br>\s*<br>", "</p><p>", content)
                return content
            except json.JSONDecodeError:
                pass

        # If content looks like HTML, sanitize it
        if "<" in content and ">" in content:
            return content

        # Plain text - convert to HTML paragraphs
        paragraphs = content.split("\n\n")
        html_parts = []
        for p in paragraphs:
            p = p.strip()
            if p:
                p = p.replace("\n", "<br>")
                html_parts.append(f"<p>{p}</p>")

        return "".join(html_parts) if html_parts else f"<p>{content}</p>"
