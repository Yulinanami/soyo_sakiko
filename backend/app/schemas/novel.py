"""小说数据结构"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class NovelSource(str, Enum):
    AO3 = "ao3"
    PIXIV = "pixiv"
    LOFTER = "lofter"
    BILIBILI = "bilibili"


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


class NovelListResponse(BaseModel):
    novels: List[Novel]
    total: int
    page: int
    page_size: int
    has_more: bool
