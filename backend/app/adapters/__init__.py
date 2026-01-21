"""适配器入口"""

from app.adapters.base import BaseAdapter
from app.adapters.ao3 import AO3Adapter
from app.adapters.pixiv import PixivAdapter
from app.adapters.lofter import LofterAdapter
from app.adapters.bilibili import BilibiliAdapter
from app.schemas.novel import NovelSource

_adapters = {
    NovelSource.AO3: AO3Adapter(),
    NovelSource.PIXIV: PixivAdapter(),
    NovelSource.LOFTER: LofterAdapter(),
    NovelSource.BILIBILI: BilibiliAdapter(),
}


def get_adapter(source: NovelSource) -> BaseAdapter:
    """按来源返回适配器"""
    if source not in _adapters:
        raise ValueError(f"No adapter available for source: {source}")
    return _adapters[source]


__all__ = [
    "BaseAdapter",
    "AO3Adapter",
    "PixivAdapter",
    "LofterAdapter",
    "BilibiliAdapter",
    "get_adapter",
]
