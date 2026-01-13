"""
Novels Router
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.adapters import get_adapter
from app.services.cache_service import cache, CacheKeys

router = APIRouter()

# Cache TTL settings (in seconds)
SEARCH_CACHE_TTL = 300  # 5 minutes
DETAIL_CACHE_TTL = 600  # 10 minutes
CHAPTER_CACHE_TTL = 1800  # 30 minutes


@router.get("", response_model=NovelListResponse)
async def search_novels(
    sources: List[NovelSource] = Query(default=[NovelSource.AO3]),
    tags: List[str] = Query(default=["素祥", "祥素"]),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    """Search novels across multiple sources with caching"""

    # Create cache key
    cache_key = CacheKeys.novel_search([s.value for s in sources], tags, page, sort_by)

    # Try to get from cache
    cached = await cache.get(cache_key)
    if cached:
        return NovelListResponse(**cached)

    # Fetch from sources
    all_novels = []
    for source in sources:
        try:
            adapter = get_adapter(source)
            novels = await adapter.search(
                tags=tags, page=page, page_size=page_size, sort_by=sort_by
            )
            all_novels.extend(novels)
        except Exception as e:
            print(f"Error fetching from {source}: {e}")

    # Sort combined results
    if sort_by == "date":
        all_novels.sort(key=lambda x: x.published_at, reverse=(sort_order == "desc"))
    elif sort_by == "kudos":
        all_novels.sort(key=lambda x: x.kudos or 0, reverse=(sort_order == "desc"))
    elif sort_by == "hits":
        all_novels.sort(key=lambda x: x.hits or 0, reverse=(sort_order == "desc"))

    # Paginate
    total = len(all_novels)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_novels[start:end]

    response = NovelListResponse(
        novels=paginated,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )

    # Cache the response
    await cache.set(cache_key, response.model_dump(), SEARCH_CACHE_TTL)

    return response


@router.get("/{source}/{novel_id}", response_model=Novel)
async def get_novel_detail(source: NovelSource, novel_id: str):
    """Get novel details with caching"""

    # Try cache first
    cache_key = CacheKeys.novel_detail(source.value, novel_id)
    cached = await cache.get(cache_key)
    if cached:
        return Novel(**cached)

    # Fetch from adapter
    adapter = get_adapter(source)
    novel = await adapter.get_detail(novel_id)

    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # Cache the result
    await cache.set(cache_key, novel.model_dump(), DETAIL_CACHE_TTL)

    return novel


@router.get("/{source}/{novel_id}/chapters")
async def get_chapters(source: NovelSource, novel_id: str):
    """Get chapter list for a novel with caching"""

    cache_key = CacheKeys.novel_chapters(source.value, novel_id)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    adapter = get_adapter(source)
    chapters = await adapter.get_chapters(novel_id)

    await cache.set(cache_key, chapters, DETAIL_CACHE_TTL)

    return chapters


@router.get("/{source}/{novel_id}/chapters/{chapter_num}")
async def get_chapter_content(source: NovelSource, novel_id: str, chapter_num: int):
    """Get chapter content with caching"""

    cache_key = CacheKeys.chapter_content(source.value, novel_id, chapter_num)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    adapter = get_adapter(source)
    content = await adapter.get_chapter_content(novel_id, chapter_num)

    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")

    await cache.set(cache_key, content, CHAPTER_CACHE_TTL)

    return content
