"""来源处理基类"""

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional
from app.schemas.novel import Novel
from app.config import settings


class BaseAdapter(ABC):
    """来源处理基类"""

    source_name: str
    max_workers: Optional[int] = None

    def __init__(self) -> None:
        """准备后台执行"""
        self._executor: Optional[ThreadPoolExecutor] = None

    def _get_executor(self) -> ThreadPoolExecutor:
        """获取后台执行工具"""
        if self._executor is None:
            workers = self.max_workers or settings.ADAPTER_MAX_WORKERS
            self._executor = ThreadPoolExecutor(max_workers=workers)
        return self._executor

    async def run_in_executor(self, func: Callable[..., Any], *args: Any) -> Any:
        """在后台执行任务"""
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
        """按标签搜索列表"""
        pass

    @abstractmethod
    async def get_detail(self, novel_id: str) -> Optional[Novel]:
        """获取详情"""
        pass

    @abstractmethod
    async def get_chapters(self, novel_id: str) -> List[dict]:
        """获取章节列表"""
        pass

    @abstractmethod
    async def get_chapter_content(
        self, novel_id: str, chapter_num: int
    ) -> Optional[str]:
        """获取章节内容"""
        pass
