"""数据库配置"""

from sqlalchemy import DateTime, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_user_data_columns():
    """为现有用户数据表补充新增的可空字段"""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    column_type = DateTime().compile(dialect=engine.dialect)
    quote = engine.dialect.identifier_preparer.quote

    with engine.begin() as connection:
        for table_name in ("favorites", "reading_history"):
            if table_name not in table_names:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "published_at" not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {quote(table_name)} "
                        f"ADD COLUMN {quote('published_at')} {column_type}"
                    )
                )


def get_db():
    """提供数据连接"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
