# 📁 app/schemas/category.py

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseResponse


class CategoryCreateRequest(BaseModel):
    name:        str           = Field(..., min_length=1, max_length=100, example="Smartphones")
    description: Optional[str] = Field(None, max_length=255)


class CategoryUpdateRequest(BaseModel):
    name:        Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class CategoryData(BaseModel):
    id:          UUID
    no:          int
    name:        str
    description: Optional[str] = None
    created_at:  datetime
    class Config:
        from_attributes = True


class CategoryCreateResponse(BaseResponse):
    code:    int  = 201
    message: str  = "Category created successfully"
    data: CategoryData


class CategoryUpdateResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Category updated successfully"
    data: CategoryData


class CategoryDetailResponse(BaseResponse):
    code:    int  = 200
    data: CategoryData


class CategoryDeleteResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Category deleted successfully"


class CategoryListResponse(BaseResponse):
    code:    int  = 200
    data: List[CategoryData]