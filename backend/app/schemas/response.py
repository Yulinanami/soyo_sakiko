"""通用返回结构"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str = "ok"
    data: Optional[T] = None
    error: Optional[str] = None
