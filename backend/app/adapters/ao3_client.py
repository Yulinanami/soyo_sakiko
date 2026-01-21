"""AO3 访问支持"""

import logging
from typing import Any, List
from app.adapters.utils import with_retries

logger = logging.getLogger(__name__)

try:
    import AO3

    AO3_AVAILABLE = True
except ImportError:
    AO3_AVAILABLE = False
    logger.warning("AO3 library not installed. Run: pip install ao3-api")


def is_available() -> bool:
    """判断是否可用"""
    return AO3_AVAILABLE


def build_search(tags: List[str], sort_column: str) -> Any:
    """创建搜索对象"""
    if not AO3_AVAILABLE:
        raise RuntimeError("AO3 不可用")
    tag_query = " OR ".join(f'"{tag}"' for tag in tags)
    return AO3.Search(
        any_field=tag_query,
        sort_column=sort_column,
        sort_direction="desc",
    )


def update_search(search: Any) -> bool:
    """更新搜索内容"""
    try:
        with_retries(
            search.update,
            retries=2,
            base_delay=0.8,
            max_delay=2.0,
            on_retry=lambda exc, attempt: logger.warning(
                "AO3 search retry %s after error: %s", attempt, exc
            ),
        )
        return True
    except Exception as exc:
        logger.warning("AO3 search update failed: %s", exc)
        return False


def get_work(novel_id: str) -> Any:
    """获取作品内容"""
    if not AO3_AVAILABLE:
        raise RuntimeError("AO3 不可用")
    return with_retries(
        lambda: AO3.Work(int(novel_id)),
        retries=2,
        base_delay=0.6,
        max_delay=2.0,
        on_retry=lambda exc, attempt: logger.warning(
            "AO3 work retry %s for %s after error: %s", attempt, novel_id, exc
        ),
    )
