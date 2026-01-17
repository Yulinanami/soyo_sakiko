"""
Novels Router
"""

import asyncio
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.schemas.response import ApiResponse
from app.adapters import get_adapter
from app.services.cache_service import cache, CacheKeys
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
DETAIL_CACHE_TTL = 600  # 10 minutes
CHAPTER_CACHE_TTL = 1800  # 30 minutes


@router.get("", response_model=ApiResponse[NovelListResponse])
async def search_novels(
    sources: List[NovelSource] = Query(default_factory=list),
    tags: List[str] = Query(default_factory=list),
    exclude_tags: List[str] = Query(default=[]),  # Tags to exclude from results
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    sort_by: str = Query(default="date"),
):
    """Search novels across multiple sources"""

    if not sources:
        return ApiResponse(
            data=NovelListResponse(
                novels=[],
                total=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )
        )

    if not tags:
        return ApiResponse(
            data=NovelListResponse(
                novels=[],
                total=0,
                page=page,
                page_size=page_size,
                has_more=False,
            )
        )

    logger.info(
        "Searching sources=%s tags=%s exclude=%s page=%s",
        [s.value for s in sources],
        tags,
        exclude_tags,
        page,
    )

    # For multiple sources, we fetch page_size from EACH source, then interleave
    # This ensures balanced display from each source
    per_source_count = page_size if len(sources) > 1 else page_size

    # Fetch from all sources in parallel
    async def fetch_from_source(source: NovelSource):
        try:
            adapter = get_adapter(source)
            novels = await adapter.search(
                tags=tags,
                exclude_tags=exclude_tags,  # Pass exclude tags
                page=page,
                page_size=per_source_count,
                sort_by=sort_by,
            )
            logger.info(
                "%s fetched %s novels (page %s)",
                source.value,
                len(novels),
                page,
            )
            return source, novels
        except Exception:
            logger.exception("Error fetching from %s", source.value)
            return source, []

    # Run all searches in parallel
    results = await asyncio.gather(*[fetch_from_source(s) for s in sources])

    # Collect novels and track if any source has more
    source_novels = {}
    any_has_more = False

    for source, novels in results:
        source_novels[source] = novels
        # If we got the full count, there might be more
        if len(novels) >= per_source_count:
            any_has_more = True
        if (
            source == NovelSource.LOFTER
            and settings.LOFTER_DYNAMIC_ENABLED
            and novels
        ):
            # Dynamic crawling doesn't expose total; allow manual "load more"
            any_has_more = True

    # If multiple sources, interleave results for balanced display
    if len(sources) > 1:
        # Interleave results from different sources
        all_novels = []
        max_len = (
            max(len(novels) for novels in source_novels.values())
            if source_novels
            else 0
        )

        for i in range(max_len):
            for source in sources:
                novels = source_novels.get(source, [])
                if i < len(novels):
                    all_novels.append(novels[i])

        logger.info(
            "Interleaved %s novels from %s sources",
            len(all_novels),
            len(sources),
        )
    else:
        # Single source - just use the novels directly
        all_novels = list(source_novels.values())[0] if source_novels else []
        logger.info("Total novels from source: %s", len(all_novels))

    # For the response, we return all fetched novels (already paginated from sources)
    response = NovelListResponse(
        novels=all_novels,
        total=len(all_novels),
        page=page,
        page_size=page_size,
        has_more=any_has_more,
    )

    return ApiResponse(data=response)


@router.get("/{source}/{novel_id}", response_model=ApiResponse[Novel])
async def get_novel_detail(source: NovelSource, novel_id: str):
    """Get novel details with caching"""

    # Try cache first
    cache_key = CacheKeys.novel_detail(source.value, novel_id)
    cached = await cache.get(cache_key)
    if cached:
        return ApiResponse(data=Novel(**cached))

    # Fetch from adapter
    adapter = get_adapter(source)
    novel = await adapter.get_detail(novel_id)

    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    # Cache the result
    await cache.set(cache_key, novel.model_dump(), DETAIL_CACHE_TTL)

    return ApiResponse(data=novel)


@router.get("/{source}/{novel_id}/chapters", response_model=ApiResponse[List[dict]])
async def get_chapters(source: NovelSource, novel_id: str):
    """Get chapter list for a novel with caching"""

    cache_key = CacheKeys.novel_chapters(source.value, novel_id)
    cached = await cache.get(cache_key)
    if cached:
        return ApiResponse(data=cached)

    adapter = get_adapter(source)
    chapters = await adapter.get_chapters(novel_id)

    await cache.set(cache_key, chapters, DETAIL_CACHE_TTL)

    return ApiResponse(data=chapters)


@router.get(
    "/{source}/{novel_id}/chapters/{chapter_num}",
    response_model=ApiResponse[str],
)
async def get_chapter_content(source: NovelSource, novel_id: str, chapter_num: int):
    """Get chapter content with caching"""

    cache_key = CacheKeys.chapter_content(source.value, novel_id, chapter_num)
    cached = await cache.get(cache_key)
    if cached:
        return ApiResponse(data=cached)

    adapter = get_adapter(source)
    content = await adapter.get_chapter_content(novel_id, chapter_num)

    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")

    await cache.set(cache_key, content, CHAPTER_CACHE_TTL)

    return ApiResponse(data=content)
