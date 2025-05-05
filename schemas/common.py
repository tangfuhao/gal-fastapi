from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
