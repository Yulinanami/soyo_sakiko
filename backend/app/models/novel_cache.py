"""同人文与正文缓存模型"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class CachedNovel(Base):
    """保存从外部来源获取到的同人文元数据"""

    __tablename__ = "cached_novels"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(20), nullable=False)
    novel_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=False)
    author_url = Column(Text)
    summary = Column(Text, nullable=False, default="")
    tags = Column(Text, nullable=False, default="[]")
    rating = Column(String(50))
    word_count = Column(Integer)
    chapter_count = Column(Integer)
    kudos = Column(Integer)
    hits = Column(Integer)
    published_at = Column(DateTime)
    updated_at = Column(DateTime)
    work_date = Column(Date)
    source_url = Column(Text, nullable=False)
    cover_image = Column(Text)
    is_complete = Column(Boolean)
    first_seen_at = Column(DateTime, server_default=func.now(), nullable=False)
    fetched_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source", "novel_id", name="uq_cached_novel_source_id"),
        Index("ix_cached_novels_source_work_date", "source", "work_date"),
    )


class CachedNovelChapter(Base):
    """保存用户实际读取过的章节正文"""

    __tablename__ = "cached_novel_chapters"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(20), nullable=False)
    novel_id = Column(String(255), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    fetched_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "novel_id",
            "chapter_number",
            name="uq_cached_chapter_source_novel_number",
        ),
        Index(
            "ix_cached_chapters_source_novel",
            "source",
            "novel_id",
        ),
    )
