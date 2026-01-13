"""
Novel Schemas
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class NovelSource(str, Enum):
    AO3 = "ao3"
    PIXIV = "pixiv"
    LOFTER = "lofter"


class Novel(BaseModel):
    id: str
    source: NovelSource
    title: str
    author: str
    author_url: Optional[str] = None
    summary: str
    tags: List[str]
    rating: Optional[str] = None
    word_count: Optional[int] = None
    chapter_count: Optional[int] = None
    kudos: Optional[int] = None
    hits: Optional[int] = None
    published_at: str
    updated_at: Optional[str] = None
    source_url: str
    cover_image: Optional[str] = None
    is_complete: Optional[bool] = None

    class Config:
        from_attributes = True


class NovelSearchParams(BaseModel):
    sources: List[NovelSource] = [NovelSource.AO3]
    tags: List[str] = ["素祥", "祥素"]
    page: int = 1
    page_size: int = 20
    sort_by: str = "date"
    sort_order: str = "desc"


class NovelListResponse(BaseModel):
    novels: List[Novel]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChapterInfo(BaseModel):
    number: int
    title: str


class ChapterContent(BaseModel):
    chapter_number: int
    title: str
    content: str
