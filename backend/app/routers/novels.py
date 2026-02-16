"""小说路由"""

import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.schemas.response import ApiResponse
from app.adapters import get_adapter
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _empty_response(page: int, page_size: int) -> ApiResponse:
    """构造空列表响应"""
    return ApiResponse(
        data=NovelListResponse(
            novels=[], total=0, page=page, page_size=page_size, has_more=False
        )
    )


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
        return _empty_response(page, page_size)
    if len(sources) != 1:
        raise HTTPException(status_code=400, detail="只支持单个来源")

    if not tags:
        return _empty_response(page, page_size)

    logger.info(
        "Searching sources=%s tags=%s exclude=%s page=%s",
        [s.value for s in sources],
        tags,
        exclude_tags,
        page,
    )

    source = sources[0]
    try:
        adapter = get_adapter(source)
        novels = await adapter.search(
            tags=tags,
            exclude_tags=exclude_tags,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
        )
        logger.info("%s fetched %s novels (page %s)", source.value, len(novels), page)
    except Exception:
        logger.exception("Error fetching from %s", source.value)
        return ApiResponse(
            status="error",
            data=NovelListResponse(
                novels=[],
                total=0,
                page=page,
                page_size=page_size,
                has_more=False,
            ),
            error=f"从 {source.value} 获取数据失败，请稍后重试",
        )

    logger.info("Total novels from source: %s", len(novels))

    # 只要有数据就显示「加载更多」，让用户可以继续翻页
    response = NovelListResponse(
        novels=novels,
        total=len(novels),
        page=page,
        page_size=page_size,
        has_more=bool(novels),
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
