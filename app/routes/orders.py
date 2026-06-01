# 📁 app/routes/orders.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles, get_current_user
from app.schemas.order import (
    OrderCreateRequest, OrderCreateResponse,
    OrderDetailResponse, OrderStatusResponse,
    OrderStatusUpdateRequest, PaymentStatusUpdateRequest,
    OrderCancelResponse, OrderData,
)
from app.services.order_service import (
    create_order, get_order_by_id,
    get_orders, update_order_status, update_payment_status,
)
from app.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


# ── POST /api/v1/orders ────────────────────────────────────────────────────────
@router.post("", response_model=OrderCreateResponse, status_code=201, summary="Create order (Admin / Staff)")
async def create(
    payload: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "staff")),
):
    order = await create_order(db, payload, current_user)
    return OrderCreateResponse(
        success=True,
        message="Order created successfully",
        data=order,
    )


# ── GET /api/v1/orders ─────────────────────────────────────────────────────────
@router.get("", response_model=PaginatedResponse[OrderData], summary="Get all orders (Admin / Manager)")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by order number"),
    status: Optional[str] = Query(None, description="pending | confirmed | shipped | delivered | cancelled"),
    payment_status: Optional[str] = Query(None, description="unpaid | partial | paid | refunded"),
    customer_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
):
    params = PaginationParams(page=page, limit=limit, search=search, sort="created_at_desc")
    orders, meta = await get_orders(
        db, params,
        status=status,
        payment_status=payment_status,
        customer_id=str(customer_id) if customer_id else None,
        warehouse_id=str(warehouse_id) if warehouse_id else None,
    )
    return PaginatedResponse[OrderData](success=True, data=orders, meta=meta)


# ── GET /api/v1/orders/{order_id} ─────────────────────────────────────────────
@router.get("/{order_id}", response_model=OrderDetailResponse, summary="Get order by ID")
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = await get_order_by_id(db, str(order_id))
    return OrderDetailResponse(success=True, data=order)


# ── PUT /api/v1/orders/{order_id}/status ──────────────────────────────────────
@router.put("/{order_id}/status", response_model=OrderStatusResponse, summary="Update order status (Admin / Manager)")
async def update_status(
    order_id: UUID,
    payload: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
):
    order = await update_order_status(db, str(order_id), payload.status, current_user)
    return OrderStatusResponse(
        success=True,
        message=f"Order status updated to '{payload.status}'",
        data=order,
    )


# ── PUT /api/v1/orders/{order_id}/payment-status ──────────────────────────────
@router.put("/{order_id}/payment-status", response_model=OrderStatusResponse, summary="Update payment status (Admin only)")
async def update_payment(
    order_id: UUID,
    payload: PaymentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    order = await update_payment_status(db, str(order_id), payload.payment_status)
    return OrderStatusResponse(
        success=True,
        message=f"Payment status updated to '{payload.payment_status}'",
        data=order,
    )


# ── POST /api/v1/orders/{order_id}/cancel ─────────────────────────────────────
@router.post("/{order_id}/cancel", response_model=OrderCancelResponse, summary="Cancel order (Admin / Manager)")
async def cancel_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
):
    order = await update_order_status(db, str(order_id), "cancelled", current_user)
    return OrderCancelResponse(
        success=True,
        message="Order cancelled successfully",
        data=order,
    )


# ── GET /api/v1/orders/my-orders ──────────────────────────────────────────────
@router.get("/my-orders", response_model=PaginatedResponse[OrderData], summary="Get my orders (Customer)")
async def my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by order number"),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
):
    from app.services.order_service import get_my_orders
    params = PaginationParams(page=page, limit=limit, search=search, sort="created_at_desc")
    orders, meta = await get_my_orders(
        db, current_user, params,
        status=status,
        payment_status=payment_status,
    )
    return PaginatedResponse[OrderData](success=True, data=orders, meta=meta)