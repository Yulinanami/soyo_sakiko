"""用户标签配置模型"""

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


class UserTagConfig(Base):
    """存储用户对每个数据源的标签配置"""

    __tablename__ = "user_tag_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source = Column(String(20), nullable=False)  # ao3/pixiv/lofter/bilibili
    tags = Column(Text, nullable=True)  # JSON array: ["素祥", "祥素"]
    exclude_tags = Column(Text, nullable=True)  # JSON array: ["all祥"]
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "source", name="uq_user_source_config"),
    )
