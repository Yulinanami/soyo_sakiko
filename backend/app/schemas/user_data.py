"""
Favorite and reading history schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FavoriteBase(BaseModel):
    novel_id: str
    source: str
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    source_url: Optional[str] = None


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteOut(FavoriteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReadingHistoryBase(BaseModel):
    novel_id: str
    source: str
    title: Optional[str] = None
    author: Optional[str] = None
    cover_url: Optional[str] = None
    source_url: Optional[str] = None
    last_chapter: Optional[int] = 1
    progress: Optional[int] = 0


class ReadingHistoryCreate(ReadingHistoryBase):
    pass


class ReadingHistoryOut(ReadingHistoryBase):
    id: int
    last_read_at: datetime

    class Config:
        from_attributes = True
