"""Pixiv 数据整理"""

from datetime import datetime
from typing import Any, List

from app.schemas.novel import Novel, NovelSource


def _parse_date(raw: str) -> str:
    """整理时间文本"""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except Exception:
        return datetime.now().isoformat()


def _build_summary(caption: str) -> str:
    """整理简介文本"""
    if caption:
        return caption[:500]
    return "暂无简介"


def parse_novel(data: dict) -> Novel:
    """整理作品信息"""
    tags: List[str] = [tag.get("name", "") for tag in data.get("tags", [])]
    published_at = _parse_date(data.get("create_date", ""))
    summary = _build_summary(data.get("caption") or "")

    return Novel(
        id=str(data.get("id", "")),
        source=NovelSource.PIXIV,
        title=data.get("title", "Unknown"),
        author=data.get("user", {}).get("name", "Unknown"),
        author_url=f"https://www.pixiv.net/users/{data.get('user', {}).get('id', '')}",
        summary=summary,
        tags=tags,
        word_count=data.get("text_length", 0),
        chapter_count=1,
        kudos=data.get("total_bookmarks", 0),
        hits=data.get("total_view", 0),
        rating=None,
        published_at=published_at,
        updated_at=published_at,
        source_url=f"https://www.pixiv.net/novel/show.php?id={data.get('id', '')}",
        cover_image=data.get("image_urls", {}).get("medium"),
        is_complete=True,
    )
