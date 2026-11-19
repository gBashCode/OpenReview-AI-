"""Common response and pagination schemas."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ResponseBase(BaseModel):
    """Base schema enforcing standard Pydantic configuration."""
    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """Pagination metadata container."""
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized wrapper for paginated collections."""
    items: List[T]
    meta: PaginationMeta
