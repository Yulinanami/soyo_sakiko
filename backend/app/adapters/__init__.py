"""
Adapters Package
"""

from app.adapters.base import BaseAdapter
from app.adapters.ao3 import AO3Adapter
from app.schemas.novel import NovelSource

# Adapter registry
_adapters = {
    NovelSource.AO3: AO3Adapter(),
}


def get_adapter(source: NovelSource) -> BaseAdapter:
    """Get adapter for a given source"""
    if source not in _adapters:
        raise ValueError(f"No adapter available for source: {source}")
    return _adapters[source]


def register_adapter(source: NovelSource, adapter: BaseAdapter):
    """Register a new adapter"""
    _adapters[source] = adapter


__all__ = ["BaseAdapter", "AO3Adapter", "get_adapter", "register_adapter"]
