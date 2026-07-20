"""小说路由"""

import json
import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.schemas.novel import Novel, NovelListResponse, NovelSource
from app.schemas.response import ApiResponse
from app.adapters import get_adapter
from app.database import get_db
from app.models.novel_cache import CachedNovel, CachedNovelChapter

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """将各来源返回的日期统一为本地无时区时间"""
    if not value:
        return None

    normalized = value.strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    for date_format in ("%d %b %Y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(normalized, date_format)
        except ValueError:
            continue
    return None


def _novel_cache_values(novel: Novel) -> dict:
    """把接口模型转换为缓存表字段"""
    published_at = _parse_datetime(novel.published_at)
    updated_at = _parse_datetime(novel.updated_at)
    effective_at = updated_at or published_at
    return {
        "source": novel.source.value,
        "novel_id": novel.id,
        "title": novel.title,
        "author": novel.author,
        "author_url": novel.author_url,
        "summary": novel.summary,
        "tags": json.dumps(novel.tags, ensure_ascii=False),
        "rating": novel.rating,
        "word_count": novel.word_count,
        "chapter_count": novel.chapter_count,
        "kudos": novel.kudos,
        "hits": novel.hits,
        "published_at": published_at,
        "updated_at": updated_at,
        "work_date": effective_at.date() if effective_at else None,
        "source_url": novel.source_url,
        "cover_image": novel.cover_image,
        "is_complete": novel.is_complete,
        "fetched_at": datetime.now(),
    }


def _cache_novels(db: Session, novels: List[Novel]) -> None:
    """按来源和作品 ID 批量写入或更新元数据"""
    if not novels:
        return

    values = [_novel_cache_values(novel) for novel in novels]
    statement = sqlite_insert(CachedNovel).values(values)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[CachedNovel.source, CachedNovel.novel_id],
        set_={
            "title": excluded.title,
            "author": excluded.author,
            "author_url": excluded.author_url,
            "summary": excluded.summary,
            "tags": excluded.tags,
            "rating": excluded.rating,
            "word_count": excluded.word_count,
            "chapter_count": excluded.chapter_count,
            "kudos": excluded.kudos,
            "hits": excluded.hits,
            "published_at": excluded.published_at,
            "updated_at": excluded.updated_at,
            "work_date": excluded.work_date,
            "source_url": excluded.source_url,
            "cover_image": excluded.cover_image,
            "is_complete": excluded.is_complete,
            "fetched_at": excluded.fetched_at,
        },
    )
    db.execute(statement)
    db.commit()


def _cache_chapter(
    db: Session,
    source: NovelSource,
    novel_id: str,
    chapter_number: int,
    content: str,
) -> None:
    """保存或更新单章正文"""
    statement = sqlite_insert(CachedNovelChapter).values(
        source=source.value,
        novel_id=novel_id,
        chapter_number=chapter_number,
        content=content,
        fetched_at=datetime.now(),
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            CachedNovelChapter.source,
            CachedNovelChapter.novel_id,
            CachedNovelChapter.chapter_number,
        ],
        set_={
            "content": statement.excluded.content,
            "fetched_at": statement.excluded.fetched_at,
        },
    )
    db.execute(statement)
    db.commit()


def _deserialize_tags(raw_tags: str) -> List[str]:
    """读取缓存中的标签列表"""
    try:
        tags = json.loads(raw_tags)
        return [str(tag) for tag in tags] if isinstance(tags, list) else []
    except (TypeError, ValueError):
        return []


def _cached_to_novel(cached: CachedNovel) -> Novel:
    """把缓存记录转换回接口模型"""
    published_at = cached.published_at or cached.updated_at
    return Novel(
        id=cached.novel_id,
        source=NovelSource(cached.source),
        title=cached.title,
        author=cached.author,
        author_url=cached.author_url,
        summary=cached.summary,
        tags=_deserialize_tags(cached.tags),
        rating=cached.rating,
        word_count=cached.word_count,
        chapter_count=cached.chapter_count,
        kudos=cached.kudos,
        hits=cached.hits,
        published_at=published_at.isoformat() if published_at else "",
        updated_at=cached.updated_at.isoformat() if cached.updated_at else None,
        source_url=cached.source_url,
        cover_image=cached.cover_image,
        is_complete=cached.is_complete,
    )


def _matches_filters(cached: CachedNovel, tags: List[str], exclude_tags: List[str]) -> bool:
    """按当前设置过滤数据库缓存"""
    stored_tags = _deserialize_tags(cached.tags)
    searchable = [cached.title, cached.summary, *stored_tags]
    normalized = [value.casefold() for value in searchable if value]

    included = not tags or any(
        tag.casefold() in value
        for tag in tags
        if tag.strip()
        for value in normalized
    )
    excluded = any(
        tag.casefold() in value
        for tag in exclude_tags
        if tag.strip()
        for value in normalized
    )
    return included and not excluded


def _sort_cached(rows: List[CachedNovel], sort_by: str) -> List[CachedNovel]:
    """在同一天内应用当前排序方式"""
    if sort_by == "kudos":
        key = lambda item: item.kudos or 0
    elif sort_by == "hits":
        key = lambda item: item.hits or 0
    elif sort_by == "wordCount":
        key = lambda item: item.word_count or 0
    else:
        key = lambda item: item.updated_at or item.published_at or datetime.min
    return sorted(rows, key=key, reverse=True)


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
    db: Session = Depends(get_db),
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
        _cache_novels(db, novels)
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


@router.get("/cached/by-date", response_model=ApiResponse[NovelListResponse])
def get_cached_novels_by_date(
    source: NovelSource = Query(...),
    tags: List[str] = Query(default_factory=list),
    exclude_tags: List[str] = Query(default=[]),
    before_date: date = Query(...),
    sort_by: str = Query(default="date"),
    db: Session = Depends(get_db),
):
    """返回指定日期之前最近一个有结果日期的缓存"""
    rows = (
        db.query(CachedNovel)
        .filter(
            CachedNovel.source == source.value,
            CachedNovel.work_date.isnot(None),
            CachedNovel.work_date < before_date,
        )
        .order_by(CachedNovel.work_date.desc())
        .all()
    )
    matching_rows = [
        row for row in rows if _matches_filters(row, tags, exclude_tags)
    ]
    if not matching_rows:
        return _empty_response(1, 0)

    result_date = matching_rows[0].work_date
    date_rows = [row for row in matching_rows if row.work_date == result_date]
    date_rows = _sort_cached(date_rows, sort_by)
    has_more = any(row.work_date < result_date for row in matching_rows)
    novels = [_cached_to_novel(row) for row in date_rows]

    return ApiResponse(
        data=NovelListResponse(
            novels=novels,
            total=len(novels),
            page=1,
            page_size=len(novels),
            has_more=has_more,
            result_date=result_date.isoformat(),
        )
    )


@router.get("/{source}/{novel_id}", response_model=ApiResponse[Novel])
async def get_novel_detail(
    source: NovelSource,
    novel_id: str,
    db: Session = Depends(get_db),
):
    """获取小说详情"""
    adapter = get_adapter(source)
    try:
        novel = await adapter.get_detail(novel_id)
    except Exception:
        logger.warning(
            "Failed to refresh detail for %s/%s, trying cache",
            source.value,
            novel_id,
        )
        novel = None

    if novel:
        _cache_novels(db, [novel])
        return ApiResponse(data=novel)

    cached = (
        db.query(CachedNovel)
        .filter(
            CachedNovel.source == source.value,
            CachedNovel.novel_id == novel_id,
        )
        .first()
    )
    if cached:
        return ApiResponse(data=_cached_to_novel(cached))

    raise HTTPException(status_code=404, detail="Novel not found")


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
async def get_chapter_content(
    source: NovelSource,
    novel_id: str,
    chapter_num: int,
    db: Session = Depends(get_db),
):
    """获取章节内容"""
    cached = (
        db.query(CachedNovelChapter)
        .filter(
            CachedNovelChapter.source == source.value,
            CachedNovelChapter.novel_id == novel_id,
            CachedNovelChapter.chapter_number == chapter_num,
        )
        .first()
    )
    if cached:
        return ApiResponse(data=cached.content)

    adapter = get_adapter(source)
    content = await adapter.get_chapter_content(novel_id, chapter_num)

    if not content:
        raise HTTPException(status_code=404, detail="Chapter not found")

    failure_markers = (
        "获取失败:",
        "获取内容失败",
        "文章内容为空",
        "请配置 LOFTER_COOKIE",
    )
    if not any(marker in content for marker in failure_markers):
        _cache_chapter(db, source, novel_id, chapter_num, content)

    return ApiResponse(data=content)
