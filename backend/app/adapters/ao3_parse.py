"""AO3 数据整理"""

from typing import Any, List

from app.adapters.utils import to_iso_date
from app.schemas.novel import Novel, NovelSource


def map_sort(sort_by: str) -> str:
    """转换排序名称"""
    mapping = {
        "date": "revised_at",
        "kudos": "kudos_count",
        "hits": "hits",
        "wordCount": "word_count",
    }
    return mapping.get(sort_by, "revised_at")


def work_to_novel(work: Any) -> Novel:
    """整理作品信息"""
    author = "Anonymous"
    author_url = None
    if getattr(work, "authors", None):
        author = work.authors[0].username
        author_url = f"https://archiveofourown.org/users/{author}"

    tags: List[str] = []
    try:
        if hasattr(work, "tags"):
            tags = [str(tag) for tag in work.tags[:20]]
    except Exception:
        tags = []

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
