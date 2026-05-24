# 📁 app/services/product_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from uuid import UUID

from app.db.models.product import Product, Category
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.utils.pagination import PaginationParams, PaginationMeta
from app.core import logger


# ── Allowed sort fields ────────────────────────────────────────────────────────
SORT_FIELDS = {
    "name_asc":        Product.name.asc(),
    "name_desc":       Product.name.desc(),
    "price_asc":       Product.price.asc(),
    "price_desc":      Product.price.desc(),
    "stock_asc":       Product.stock.asc(),
    "stock_desc":      Product.stock.desc(),
    "created_at_asc":  Product.created_at.asc(),
    "created_at_desc": Product.created_at.desc(),
}


# ── Helper: build product query with category ──────────────────────────────────
def _base_query():
    return (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.is_deleted == False)
    )


# ── Create product ─────────────────────────────────────────────────────────────
async def create_product(db: AsyncSession, payload: ProductCreateRequest) -> Product:
    logger.info(f"Create product | sku={payload.sku}")

    # Check SKU unique
    result = await db.execute(
        select(Product).where(Product.sku == payload.sku, Product.is_deleted == False)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    # Check barcode unique
    if payload.barcode:
        result = await db.execute(
            select(Product).where(Product.barcode == payload.barcode, Product.is_deleted == False)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already exists")

    # Check category exists
    if payload.category_id:
        result = await db.execute(
            select(Category).where(Category.id == payload.category_id, Category.is_deleted == False)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    product = Product(
        name=payload.name,
        brand=payload.brand,
        sku=payload.sku,
        barcode=payload.barcode,
        description=payload.description,
        image_url=payload.image_url,
        price=payload.price,
        cost_price=payload.cost_price,
        stock=payload.stock,
        low_stock_threshold=payload.low_stock_threshold,
        category_id=payload.category_id,
        status=payload.status,
    )
    db.add(product)
    await db.flush()

    # Reload with category
    result = await db.execute(_base_query().where(Product.id == product.id))
    product = result.scalar_one()

    logger.info(f"Product created | id={product.id} sku={product.sku}")
    return product


# ── Get product by ID ──────────────────────────────────────────────────────────
async def get_product_by_id(db: AsyncSession, product_id: str) -> Product:
    result = await db.execute(
        _base_query().where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# ── Get all products with pagination, filter, search ──────────────────────────
async def get_products(
    db: AsyncSession,
    params: PaginationParams,
    category_id: str = None,
    status: str = None,
    min_price: float = None,
    max_price: float = None,
    low_stock: bool = None,
) -> tuple[list[Product], PaginationMeta]:
    logger.info(f"Get products | page={params.page} search={params.search}")

    query = _base_query()

    # Search by name, sku, barcode, brand
    if params.search:
        kw = f"%{params.search}%"
        query = query.where(
            or_(
                Product.name.ilike(kw),
                Product.sku.ilike(kw),
                Product.barcode.ilike(kw),
                Product.brand.ilike(kw),
            )
        )

    # Filters
    if category_id:
        query = query.where(Product.category_id == category_id)
    if status:
        query = query.where(Product.status == status)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if low_stock:
        query = query.where(Product.stock <= Product.low_stock_threshold)

    # Count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Sort + paginate
    order = SORT_FIELDS.get(params.sort, Product.created_at.desc())
    query = query.order_by(order).offset(params.offset).limit(params.limit)

    result = await db.execute(query)
    products = list(result.scalars().all())

    total_pages = (total + params.limit - 1) // params.limit
    meta = PaginationMeta(total=total, page=params.page, limit=params.limit, total_pages=total_pages)

    return products, meta


# ── Update product ─────────────────────────────────────────────────────────────
async def update_product(db: AsyncSession, product_id: str, payload: ProductUpdateRequest) -> Product:
    logger.info(f"Update product | id={product_id}")

    product = await get_product_by_id(db, product_id)

    # Check SKU unique if changed
    if payload.sku and payload.sku != product.sku:
        result = await db.execute(
            select(Product).where(Product.sku == payload.sku, Product.is_deleted == False, Product.id != product.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    # Check barcode unique if changed
    if payload.barcode and payload.barcode != product.barcode:
        result = await db.execute(
            select(Product).where(Product.barcode == payload.barcode, Product.is_deleted == False, Product.id != product.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Barcode already exists")

    # Check category exists if changed
    if payload.category_id:
        result = await db.execute(
            select(Category).where(Category.id == payload.category_id, Category.is_deleted == False)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Apply updates — only fields that are provided
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await db.flush()

    # Reload with category
    result = await db.execute(_base_query().where(Product.id == product.id))
    product = result.scalar_one()

    logger.info(f"Product updated | id={product.id}")
    return product


# ── Soft delete product ────────────────────────────────────────────────────────
async def delete_product(db: AsyncSession, product_id: str) -> None:
    logger.info(f"Delete product | id={product_id}")
    product = await get_product_by_id(db, product_id)
    product.is_deleted = True
    await db.flush()
    logger.info(f"Product deleted | id={product_id}")