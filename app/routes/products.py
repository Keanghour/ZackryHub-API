# 📁 app/routes/products.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles, get_current_user
from app.schemas.product import (
    ProductCreateRequest, ProductCreateResponse,
    ProductUpdateRequest, ProductUpdateResponse,
    ProductDetailResponse, ProductDeleteResponse,
    ProductData, CategoryItem,
)
from app.services.product_service import (
    create_product, get_product_by_id,
    get_products, update_product, delete_product,
)
from app.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


# ── Helper: build ProductData from ORM ────────────────────────────────────────
def to_product_data(p) -> ProductData:
    return ProductData(
        id=p.id,
        no=p.no,
        name=p.name,
        brand=p.brand,
        sku=p.sku,
        barcode=p.barcode,
        description=p.description,
        image_url=p.image_url,
        price=p.price,
        cost_price=p.cost_price,
        stock=p.stock,
        low_stock_threshold=p.low_stock_threshold,
        status=p.status,
        category=CategoryItem(id=p.category.id, name=p.category.name) if p.category else None,
        created_at=p.created_at,
    )


# ── POST /api/v1/products ──────────────────────────────────────────────────────
@router.post("", response_model=ProductCreateResponse, status_code=201, summary="Create product (Admin only)")
async def create(
    payload: ProductCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    product = await create_product(db, payload)
    return ProductCreateResponse(
        success=True,
        message="Product created successfully",
        data=to_product_data(product),
    )


# ── GET /api/v1/products ───────────────────────────────────────────────────────
@router.get("", response_model=PaginatedResponse[ProductData], summary="Get all products")
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by name, sku, barcode, brand"),
    sort: str = Query("created_at_desc", description="name_asc | name_desc | price_asc | price_desc | stock_asc | stock_desc | created_at_asc | created_at_desc"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="active | inactive | out_of_stock"),
    min_price: Optional[float] = Query(None, description="Min price"),
    max_price: Optional[float] = Query(None, description="Max price"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock products"),
):
    params = PaginationParams(page=page, limit=limit, search=search, sort=sort)
    products, meta = await get_products(
        db, params,
        category_id=str(category_id) if category_id else None,
        status=status,
        min_price=min_price,
        max_price=max_price,
        low_stock=low_stock,
    )
    return PaginatedResponse[ProductData](
        success=True,
        data=[to_product_data(p) for p in products],
        meta=meta,
    )


# ── GET /api/v1/products/{product_id} ─────────────────────────────────────────
@router.get("/{product_id}", response_model=ProductDetailResponse, summary="Get product by ID")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = await get_product_by_id(db, str(product_id))
    return ProductDetailResponse(success=True, data=to_product_data(product))


# ── PUT /api/v1/products/{product_id} ─────────────────────────────────────────
@router.put("/{product_id}", response_model=ProductUpdateResponse, summary="Update product (Admin only)")
async def update(
    product_id: UUID,
    payload: ProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    product = await update_product(db, str(product_id), payload)
    return ProductUpdateResponse(
        success=True,
        message="Product updated successfully",
        data=to_product_data(product),
    )


# ── DELETE /api/v1/products/{product_id} ──────────────────────────────────────
@router.delete("/{product_id}", response_model=ProductDeleteResponse, summary="Delete product (Admin only)")
async def delete(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    await delete_product(db, str(product_id))
    return ProductDeleteResponse(success=True, message="Product deleted successfully")