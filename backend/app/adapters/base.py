"""
Base Adapter Class
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.novel import Novel


class BaseAdapter(ABC):
    """Abstract base class for data source adapters"""

    source_name: str

    @abstractmethod
    async def search(
        self,
        tags: List[str],
        exclude_tags: List[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "date",
    ) -> List[Novel]:
        """Search for novels by tags"""
        pass

    @abstractmethod
    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """Get novel details"""
        pass

    @abstractmethod
    async def get_chapters(self, novel_id: str) -> List[dict]:
        """Get chapter list"""
        pass

    @abstractmethod
    async def get_chapter_content(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """Get chapter content"""
        pass
