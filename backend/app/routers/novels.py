"""
Novels Router
"""

import asyncio
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.adapters import get_adapter
from app.services.cache_service import cache, CacheKeys
from app.config import settings

router = APIRouter()

# Cache TTL settings (in seconds)
SEARCH_CACHE_TTL = 300  # 5 minutes
DETAIL_CACHE_TTL = 600  # 10 minutes
CHAPTER_CACHE_TTL = 1800  # 30 minutes


@router.get("", response_model=NovelListResponse)
async def search_novels(
    sources: List[NovelSource] = Query(default_factory=list),
    tags: List[str] = Query(default_factory=list),
    exclude_tags: List[str] = Query(default=[]),  # Tags to exclude from results
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    """Search novels across multiple sources"""

    if not sources:
        return NovelListResponse(
            novels=[],
            total=0,
            page=page,
            page_size=page_size,
            has_more=False,
        )

    if not tags:
        return NovelListResponse(
            novels=[],
            total=0,
            page=page,
            page_size=page_size,
            has_more=False,
        )

    print(
        f"🔍 Searching sources: {[s.value for s in sources]}, tags: {tags}, exclude: {exclude_tags}, page: {page}"
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
            print(f"✅ {source.value}: fetched {len(novels)} novels (page {page})")
            return source, novels
        except Exception as e:
            print(f"❌ Error fetching from {source.value}: {e}")
            import traceback

            traceback.print_exc()
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

        print(f"📚 Interleaved {len(all_novels)} novels from {len(sources)} sources")
    else:
        # Single source - just use the novels directly
        all_novels = list(source_novels.values())[0] if source_novels else []
        print(f"📚 Total novels from source: {len(all_novels)}")

    # For the response, we return all fetched novels (already paginated from sources)
    response = NovelListResponse(
        novels=all_novels,
        total=len(all_novels) + (page_size if any_has_more else 0),  # Estimate total
        page=page,
        page_size=page_size,
        has_more=any_has_more,
    )

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
