"""用户数据路由"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.favorite import Favorite, ReadingHistory
from app.routers.auth import get_current_user
from app.schemas.response import ApiResponse
from app.schemas.user_data import (
    FavoriteCreate,
    FavoriteOut,
    ReadingHistoryCreate,
    ReadingHistoryOut,
)

router = APIRouter()


@router.get("/favorites", response_model=ApiResponse[list[FavoriteOut]])
def list_favorites(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """获取收藏列表"""
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return ApiResponse(data=[FavoriteOut.model_validate(item) for item in favorites])


@router.post("/favorites", response_model=ApiResponse[FavoriteOut])
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """添加或更新收藏"""
    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.novel_id == payload.novel_id,
            Favorite.source == payload.source,
        )
        .first()
    )
    if favorite:
        favorite.title = payload.title or favorite.title
        favorite.author = payload.author or favorite.author
        favorite.cover_url = payload.cover_url or favorite.cover_url
        favorite.source_url = payload.source_url or favorite.source_url
    else:
        favorite = Favorite(
            user_id=current_user.id,
            novel_id=payload.novel_id,
            source=payload.source,
            title=payload.title,
            author=payload.author,
            cover_url=payload.cover_url,
            source_url=payload.source_url,
        )
        db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return ApiResponse(data=FavoriteOut.model_validate(favorite))


@router.delete("/favorites/{favorite_id}", response_model=ApiResponse[None])
def delete_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除收藏"""
    favorite = (
        db.query(Favorite)
        .filter(Favorite.id == favorite_id, Favorite.user_id == current_user.id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()
    return ApiResponse()


@router.get("/history", response_model=ApiResponse[list[ReadingHistoryOut]])
def list_history(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """获取阅读记录"""
    ttl_days = settings.READING_HISTORY_TTL_DAYS
    cutoff = None
    if ttl_days and ttl_days > 0:
        cutoff = datetime.now() - timedelta(days=ttl_days)
        db.query(ReadingHistory).filter(
            ReadingHistory.user_id == current_user.id,
            ReadingHistory.last_read_at < cutoff,
        ).delete()
        db.commit()

    query = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id)
    if cutoff:
        query = query.filter(ReadingHistory.last_read_at >= cutoff)
    records = query.order_by(ReadingHistory.last_read_at.desc()).all()
    return ApiResponse(
        data=[ReadingHistoryOut.model_validate(item) for item in records]
    )


@router.post("/history", response_model=ApiResponse[ReadingHistoryOut])
def record_history(
    payload: ReadingHistoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """添加或更新阅读记录"""
    record = (
        db.query(ReadingHistory)
        .filter(
            ReadingHistory.user_id == current_user.id,
            ReadingHistory.novel_id == payload.novel_id,
            ReadingHistory.source == payload.source,
        )
        .first()
    )
    if record:
        record.title = payload.title or record.title
        record.author = payload.author or record.author
        record.cover_url = payload.cover_url or record.cover_url
        record.source_url = payload.source_url or record.source_url
        record.last_chapter = payload.last_chapter or record.last_chapter
        record.progress = payload.progress or record.progress
        record.last_read_at = datetime.now()
    else:
        record = ReadingHistory(
            user_id=current_user.id,
            novel_id=payload.novel_id,
            source=payload.source,
            title=payload.title,
            author=payload.author,
            cover_url=payload.cover_url,
            source_url=payload.source_url,
            last_chapter=payload.last_chapter or 1,
            progress=payload.progress or 0,
            last_read_at=datetime.now(),
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return ApiResponse(data=ReadingHistoryOut.model_validate(record))


@router.delete("/history/{history_id}", response_model=ApiResponse[None])
def delete_history(
    history_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除阅读记录"""
    record = (
        db.query(ReadingHistory)
        .filter(
            ReadingHistory.id == history_id, ReadingHistory.user_id == current_user.id
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="History not found")
    db.delete(record)
    db.commit()
    return ApiResponse()
