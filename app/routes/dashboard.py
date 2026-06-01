# 📁 app/routes/dashboard.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles
from app.schemas.dashboard import StatsResponse, LowStockResponse, RecentOrdersResponse
from app.services.dashboard_service import get_stats, get_low_stock, get_recent_orders

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


# ── GET /api/v1/dashboard/stats ───────────────────────────────────────────────
@router.get("/stats", response_model=StatsResponse, summary="Get dashboard stats (Admin / Manager)")
async def stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
):
    data = await get_stats(db)
    return StatsResponse(success=True, data=data)


# ── GET /api/v1/dashboard/low-stock ──────────────────────────────────────────
@router.get("/low-stock", response_model=LowStockResponse, summary="Get low stock products (Admin / Manager)")
async def low_stock(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
    limit: int = Query(20, ge=1, le=100, description="Max number of products to return"),
):
    data = await get_low_stock(db, limit=limit)
    return LowStockResponse(success=True, data=data)


# ── GET /api/v1/dashboard/recent-orders ──────────────────────────────────────
@router.get("/recent-orders", response_model=RecentOrdersResponse, summary="Get recent orders (Admin / Manager)")
async def recent_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin", "manager")),
    limit: int = Query(10, ge=1, le=50, description="Max number of orders to return"),
):
    data = await get_recent_orders(db, limit=limit)
    return RecentOrdersResponse(success=True, data=data)