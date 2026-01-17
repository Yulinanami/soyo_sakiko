"""
Pixiv Adapter for fetching novels

Pixiv requires OAuth authentication with a refresh token.
Users need to obtain their refresh token using: https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362
"""

import logging
from typing import List, Optional
from datetime import datetime

from app.adapters.base import BaseAdapter
from app.adapters.utils import exclude, with_retries
from app.schemas.novel import Novel, NovelSource
from app.config import settings

logger = logging.getLogger(__name__)


class PixivAdapter(BaseAdapter):
    """Adapter for Pixiv novel data source"""

    def __init__(self):
        super().__init__()
        self._api = None
        self._token = None

    def reset(self) -> None:
        """Clear cached API client so credentials are re-read."""
        self._api = None
        self._token = None

    def _init_api(self):
        """Initialize Pixiv API with refresh token"""
        refresh_token = settings.PIXIV_REFRESH_TOKEN
        if not refresh_token:
            logger.warning("Pixiv: no refresh token configured")
            self._api = None
            self._token = None
            return False
        if self._api is not None and self._token == refresh_token:
            return True

        try:
            from pixivpy3 import AppPixivAPI

            self._api = AppPixivAPI()
            self._api.auth(refresh_token=refresh_token)
            self._token = refresh_token
            logger.info("Pixiv API authenticated successfully")
            return True
        except ImportError:
            logger.warning("Pixiv: pixivpy3 not installed. Run: pip install pixivpy3")
            return False
        except Exception as e:
            logger.exception("Pixiv authentication failed")
            self._api = None
            return False

    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """Search Pixiv novels by tags"""
        if not self._init_api():
            return []

        exclude_tags = exclude_tags or []

        # Search each tag separately and combine results
        search_tags = tags if tags else ["素祥"]

        def _search():
            try:
                all_novels = []
                seen_ids = set()

                # Pixiv uses offset-based pagination
                offset = (page - 1) * page_size

                for tag in search_tags:
                    try:
                        # Search for novels with the tag
                        result = with_retries(
                            lambda: self._api.search_novel(
                                word=tag,
                                sort="date_desc"
                                if sort_by == "date"
                                else "popular_desc",
                                search_target="partial_match_for_tags",
                                offset=offset,  # Use offset for pagination
                            ),
                            retries=2,
                            base_delay=0.8,
                            max_delay=2.0,
                            on_retry=lambda exc, attempt: logger.warning(
                                "Pixiv search retry %s for tag %s after error: %s",
                                attempt,
                                tag,
                                exc,
                            ),
                        )

                        for novel_data in result.get("novels", []):
                            novel_id = novel_data.get("id")
                            if novel_id in seen_ids:
                                continue
                            seen_ids.add(novel_id)

                            # Filter by title - exclude works containing exclude_tags
                            title = novel_data.get("title", "")
                            if exclude(title, exclude_tags):
                                continue
                            all_novels.append(self._parse_novel(novel_data))
                    except Exception as e:
                        logger.exception("Pixiv search error for tag %s", tag)
                        continue

                # Sort by date and return page_size items
                all_novels.sort(key=lambda x: x.published_at or "", reverse=True)
                return all_novels[:page_size]
            except Exception as e:
                logger.exception("Pixiv search error")
                return []

        return await self.run_in_executor(_search)

    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """Get novel detail by ID"""
        if not self._init_api():
            return None

        def _get_detail():
            try:
                result = with_retries(
                    lambda: self._api.novel_detail(int(novel_id)),
                    retries=2,
                    base_delay=0.6,
                    max_delay=2.0,
                    on_retry=lambda exc, attempt: logger.warning(
                        "Pixiv detail retry %s for %s after error: %s",
                        attempt,
                        novel_id,
                        exc,
                    ),
                )
                if "novel" in result:
                    return self._parse_novel(result["novel"])
                return None
            except Exception as e:
                logger.exception("Pixiv detail error for %s", novel_id)
                return None

        return await self.run_in_executor(_get_detail)

    async def get_chapters(self, novel_id: str) -> List[dict]:
        """Get chapter list for a novel"""
        # Pixiv novels are typically single chapter
        # For series, we would need different handling
        return [{"chapter": 1, "title": "正文"}]

    async def get_chapter_content(self, novel_id: str, chapter: int) -> Optional[str]:
        """Get chapter content"""
        if not self._init_api():
            return None

        def _get_content():
            try:
                result = with_retries(
                    lambda: self._api.novel_text(int(novel_id)),
                    retries=2,
                    base_delay=0.6,
                    max_delay=2.0,
                    on_retry=lambda exc, attempt: logger.warning(
                        "Pixiv content retry %s for %s after error: %s",
                        attempt,
                        novel_id,
                        exc,
                    ),
                )
                if "novel_text" in result:
                    # Convert newlines to HTML paragraphs
                    text = result["novel_text"]
                    paragraphs = text.split("\n")
                    html = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
                    return html
                return None
            except Exception as e:
                logger.exception("Pixiv content error for %s", novel_id)
                return None

        return await self.run_in_executor(_get_content)

    def _parse_novel(self, data: dict) -> Novel:
        """Parse Pixiv novel data into unified Novel schema"""
        # Extract tags
        tags = [tag.get("name", "") for tag in data.get("tags", [])]

        # Parse date
        create_date = data.get("create_date", "")
        try:
            published_at = datetime.fromisoformat(
                create_date.replace("Z", "+00:00")
            ).isoformat()
        except:
            published_at = datetime.now().isoformat()

        # Get summary/caption, default to empty string
        caption = data.get("caption") or ""
        summary = caption[:500] if caption else "暂无简介"

        return Novel(
            id=str(data.get("id", "")),
            source=NovelSource.PIXIV,
            title=data.get("title", "Unknown"),
            author=data.get("user", {}).get("name", "Unknown"),
            author_url=f"https://www.pixiv.net/users/{data.get('user', {}).get('id', '')}",
            summary=summary,
            tags=tags,
            word_count=data.get("text_length", 0),
            chapter_count=1,  # Most Pixiv novels are single-chapter
            kudos=data.get("total_bookmarks", 0),
            hits=data.get("total_view", 0),
            rating=None,  # Pixiv doesn't have ratings like AO3
            published_at=published_at,
            updated_at=published_at,
            source_url=f"https://www.pixiv.net/novel/show.php?id={data.get('id', '')}",
            cover_image=data.get("image_urls", {}).get("medium"),
            is_complete=True,
        )
