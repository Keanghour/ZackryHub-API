# 📁 app/routes/inventory.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles
from app.schemas.inventory import (
    StockInRequest, StockInResponse,
    StockOutRequest, StockOutResponse,
    StockAdjustRequest, StockAdjustResponse,
    InventoryLogData,
)
from app.services.inventory_service import (
    stock_in, stock_out, stock_adjust,
    get_inventory_logs, to_log_data,
)
from app.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


# ── POST /api/v1/inventory/stock-in 
@router.post("/stock-in", response_model=StockInResponse, status_code=201, summary="Stock in (Admin / Manager / Staff)")
async def do_stock_in(
    payload: StockInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager", "staff")),
):
    log = await stock_in(db, payload, current_user)
    return StockInResponse(success=True, message="Stock added successfully", data=log)


# ── POST /api/v1/inventory/stock-out 
@router.post("/stock-out", response_model=StockOutResponse, status_code=201, summary="Stock out (Admin / Manager / Staff)")
async def do_stock_out(
    payload: StockOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager", "staff")),
):
    log = await stock_out(db, payload, current_user)
    return StockOutResponse(success=True, message="Stock removed successfully", data=log)


# ── POST /api/v1/inventory/adjust 
@router.post("/adjust", response_model=StockAdjustResponse, status_code=201, summary="Stock adjustment (Admin / Manager only)")
async def do_adjust(
    payload: StockAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
):
    log = await stock_adjust(db, payload, current_user)
    return StockAdjustResponse(success=True, message="Stock adjusted successfully", data=log)


# ── GET /api/v1/inventory/logs 
@router.get("/logs", response_model=PaginatedResponse[InventoryLogData], summary="Get inventory logs (Admin / Manager)")
async def list_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by product name or SKU"),
    product_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    movement_type: Optional[str] = Query(None, description="stock_in | stock_out | adjustment"),
):
    params = PaginationParams(page=page, limit=limit, search=search, sort="created_at_desc")
    logs, meta = await get_inventory_logs(
        db, params,
        product_id=str(product_id) if product_id else None,
        warehouse_id=str(warehouse_id) if warehouse_id else None,
        movement_type=movement_type,
    )
    return PaginatedResponse[InventoryLogData](
        success=True,
        data=[to_log_data(log) for log in logs],
        meta=meta,
    )