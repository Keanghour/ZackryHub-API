# 📁 app/routes/categories.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles, get_current_user
from app.schemas.category import (
    CategoryCreateRequest, CategoryCreateResponse,
    CategoryUpdateRequest, CategoryUpdateResponse,
    CategoryDetailResponse, CategoryDeleteResponse,
    CategoryListResponse, CategoryData,
)
from app.services.category_service import (
    create_category, get_all_categories,
    get_category_by_id, update_category, delete_category,
)

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


# ── POST /api/v1/categories ────────────────────────────────────────────────────
@router.post("", response_model=CategoryCreateResponse, status_code=201, summary="Create category (Admin only)")
async def create(
    payload: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    category = await create_category(db, payload)
    return CategoryCreateResponse(
        success=True,
        message="Category created successfully",
        data=CategoryData.model_validate(category),
    )


# ── GET /api/v1/categories ─────────────────────────────────────────────────────
@router.get("", response_model=CategoryListResponse, summary="Get all categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: str = Query(None, description="Search by name or description"),
):
    categories = await get_all_categories(db, search=search)
    return CategoryListResponse(
        success=True,
        data=[CategoryData.model_validate(c) for c in categories],
    )


# ── GET /api/v1/categories/{category_id} ──────────────────────────────────────
@router.get("/{category_id}", response_model=CategoryDetailResponse, summary="Get category by ID")
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = await get_category_by_id(db, str(category_id))
    return CategoryDetailResponse(
        success=True,
        data=CategoryData.model_validate(category),
    )


# ── PUT /api/v1/categories/{category_id} ──────────────────────────────────────
@router.put("/{category_id}", response_model=CategoryUpdateResponse, summary="Update category (Admin only)")
async def update(
    category_id: UUID,
    payload: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    category = await update_category(db, str(category_id), payload)
    return CategoryUpdateResponse(
        success=True,
        message="Category updated successfully",
        data=CategoryData.model_validate(category),
    )


# ── DELETE /api/v1/categories/{category_id} ───────────────────────────────────
@router.delete("/{category_id}", response_model=CategoryDeleteResponse, summary="Delete category (Admin only)")
async def delete(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    await delete_category(db, str(category_id))
    return CategoryDeleteResponse(
        success=True,
        message="Category deleted successfully",
    )