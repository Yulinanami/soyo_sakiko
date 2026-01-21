"""小说路由"""

import asyncio
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.schemas.response import ApiResponse
from app.adapters import get_adapter
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=ApiResponse[NovelListResponse])
async def search_novels(
    sources: List[NovelSource] = Query(default_factory=list),
    tags: List[str] = Query(default_factory=list),
    exclude_tags: List[str] = Query(default=[]),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    sort_by: str = Query(default="date"),
):
    """按来源和标签搜索小说"""

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

    per_source_count = page_size if len(sources) > 1 else page_size

    async def fetch_from_source(source: NovelSource):
        """从单一来源获取列表"""
        try:
            adapter = get_adapter(source)
            novels = await adapter.search(
                tags=tags,
                exclude_tags=exclude_tags,
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

    results = await asyncio.gather(*[fetch_from_source(s) for s in sources])

    source_novels = {}
    any_has_more = False

    for source, novels in results:
        source_novels[source] = novels
        if len(novels) >= per_source_count:
            any_has_more = True
        if source == NovelSource.LOFTER and settings.LOFTER_DYNAMIC_ENABLED and novels:
            any_has_more = True
        if source == NovelSource.BILIBILI and novels:
            any_has_more = True

    if len(sources) > 1:
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
        all_novels = list(source_novels.values())[0] if source_novels else []
        logger.info("Total novels from source: %s", len(all_novels))

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
    """获取小说详情"""
    adapter = get_adapter(source)
    novel = await adapter.get_detail(novel_id)

    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    return ApiResponse(data=novel)


@router.get("/{source}/{novel_id}/chapters", response_model=ApiResponse[List[dict]])
async def get_chapters(source: NovelSource, novel_id: str):
    """获取章节列表"""
    adapter = get_adapter(source)
    chapters = await adapter.get_chapters(novel_id)

    return ApiResponse(data=chapters)


@router.get(
    "/{source}/{novel_id}/chapters/{chapter_num}",
    response_model=ApiResponse[str],
)
async def get_chapter_content(source: NovelSource, novel_id: str, chapter_num: int):
    """获取章节内容"""
    adapter = get_adapter(source)
    content = await adapter.get_chapter_content(novel_id, chapter_num)

    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return ApiResponse(data=content)
