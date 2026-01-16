"""
Favorite Model
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from app.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    novel_id = Column(String(255), nullable=False)
    source = Column(String(20), nullable=False)
    title = Column(String(500))
    author = Column(String(100))
    cover_url = Column(Text)
    source_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "novel_id", "source", name="uq_user_novel_source"),
    )


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    novel_id = Column(String(255), nullable=False)
    source = Column(String(20), nullable=False)
    title = Column(String(500))
    author = Column(String(100))
    cover_url = Column(Text)
    source_url = Column(Text)
    last_chapter = Column(Integer, default=1)
    progress = Column(Integer, default=0)  # percentage
    last_read_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "novel_id", "source", name="uq_history_user_novel_source"),
    )
