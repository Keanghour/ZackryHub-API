# 📁 app/utils/pagination.py

from fastapi import Query
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=100, description="Items per page"),
        search: str = Query(None, description="Search keyword"),
        sort: str = Query("created_at_desc", description="Sort e.g. name_asc, email_desc"),
    ):
        self.page = page
        self.limit = limit
        self.search = search
        self.sort = sort

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    meta: PaginationMeta