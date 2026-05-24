# 📁 app/schemas/category.py

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Create ─────────────────────────────────────────────────────────────────────
class CategoryCreateRequest(BaseModel):
    name:        str           = Field(..., min_length=1, max_length=100, example="Smartphones")
    description: Optional[str] = Field(None, max_length=255, example="Mobile phones and smartphones")


# ── Update ─────────────────────────────────────────────────────────────────────
class CategoryUpdateRequest(BaseModel):
    name:        Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


# ── Data ───────────────────────────────────────────────────────────────────────
class CategoryData(BaseModel):
    id:          UUID
    no:          int
    name:        str
    description: Optional[str] = None
    created_at:  datetime

    class Config:
        from_attributes = True


# ── Responses ──────────────────────────────────────────────────────────────────
class CategoryCreateResponse(BaseModel):
    success: bool = True
    message: str  = "Category created successfully"
    data: CategoryData


class CategoryUpdateResponse(BaseModel):
    success: bool = True
    message: str  = "Category updated successfully"
    data: CategoryData


class CategoryDetailResponse(BaseModel):
    success: bool = True
    data: CategoryData


class CategoryDeleteResponse(BaseModel):
    success: bool = True
    message: str  = "Category deleted successfully"


class CategoryListResponse(BaseModel):
    success: bool = True
    data: list[CategoryData]