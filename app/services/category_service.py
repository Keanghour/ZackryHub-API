# 📁 app/services/category_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from app.db.models.product import Category
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.core import logger


# ── Create category ────────────────────────────────────────────────────────────
async def create_category(db: AsyncSession, payload: CategoryCreateRequest) -> Category:
    logger.info(f"Create category | name={payload.name}")

    # Check name unique (case-insensitive)
    result = await db.execute(
        select(Category).where(
            func.lower(Category.name) == payload.name.lower().strip(),
            Category.is_deleted == False,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists",
        )

    category = Category(
        name=payload.name.strip(),
        description=payload.description,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)

    logger.info(f"Category created | id={category.id} name={category.name}")
    return category


# ── Get all categories ─────────────────────────────────────────────────────────
async def get_all_categories(db: AsyncSession, search: str = None) -> list[Category]:
    logger.info(f"Get categories | search={search}")

    query = select(Category).where(Category.is_deleted == False)

    if search:
        kw = f"%{search}%"
        query = query.where(
            or_(
                Category.name.ilike(kw),
                Category.description.ilike(kw),
            )
        )

    query = query.order_by(Category.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


# ── Get category by ID ─────────────────────────────────────────────────────────
async def get_category_by_id(db: AsyncSession, category_id: str) -> Category:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.is_deleted == False,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


# ── Update category ────────────────────────────────────────────────────────────
async def update_category(
    db: AsyncSession,
    category_id: str,
    payload: CategoryUpdateRequest,
) -> Category:
    logger.info(f"Update category | id={category_id}")

    category = await get_category_by_id(db, category_id)

    # Check name unique if changed
    if payload.name and payload.name.strip().lower() != category.name.lower():
        result = await db.execute(
            select(Category).where(
                func.lower(Category.name) == payload.name.lower().strip(),
                Category.is_deleted == False,
                Category.id != category.id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{payload.name}' already exists",
            )
        category.name = payload.name.strip()

    if payload.description is not None:
        category.description = payload.description

    await db.flush()
    await db.refresh(category)

    logger.info(f"Category updated | id={category.id}")
    return category


# ── Soft delete category ───────────────────────────────────────────────────────
async def delete_category(db: AsyncSession, category_id: str) -> None:
    logger.info(f"Delete category | id={category_id}")

    category = await get_category_by_id(db, category_id)

    # Check if category has active products
    from app.db.models.product import Product
    result = await db.execute(
        select(func.count()).select_from(Product).where(
            Product.category_id == category.id,
            Product.is_deleted == False,
        )
    )
    product_count = result.scalar_one()

    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category — it has {product_count} active product(s). Reassign them first.",
        )

    category.is_deleted = True
    await db.flush()
    logger.info(f"Category deleted | id={category_id}")