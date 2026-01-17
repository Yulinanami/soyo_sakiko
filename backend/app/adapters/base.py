"""
Base Adapter Class
"""

from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional

from app.schemas.novel import Novel


class BaseAdapter(ABC):
    """Abstract base class for data source adapters"""

    source_name: str
    _executor: Optional[ThreadPoolExecutor] = None

    def _get_executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=2)
        return self._executor

    async def run_in_executor(self, func: Callable[..., Any], *args: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._get_executor(), func, *args)

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
