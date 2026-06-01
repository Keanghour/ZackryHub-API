# 📁 app/services/dashboard_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models.user import User
from app.db.models.product import Product
from app.db.models.order import Order, OrderItem
from app.schemas.dashboard import DashboardStats, LowStockItem, RecentOrderItem
from app.core import logger


# ── Get dashboard stats ────────────────────────────────────────────────────────
async def get_stats(db: AsyncSession) -> DashboardStats:
    logger.info("Get dashboard stats")

    # Total users (non-deleted)
    result = await db.execute(
        select(func.count(User.id)).where(User.is_deleted == False)
    )
    total_users = result.scalar_one()

    # Total products (non-deleted)
    result = await db.execute(
        select(func.count(Product.id)).where(Product.is_deleted == False)
    )
    total_products = result.scalar_one()

    # Total orders + by status
    result = await db.execute(
        select(func.count(Order.id)).where(Order.is_deleted == False)
    )
    total_orders = result.scalar_one()

    result = await db.execute(
        select(func.count(Order.id)).where(
            Order.status == "pending",
            Order.is_deleted == False,
        )
    )
    pending_orders = result.scalar_one()

    result = await db.execute(
        select(func.count(Order.id)).where(
            Order.status == "confirmed",
            Order.is_deleted == False,
        )
    )
    confirmed_orders = result.scalar_one()

    # Total revenue (sum of grand_total for delivered orders)
    result = await db.execute(
        select(func.coalesce(func.sum(Order.grand_total), 0)).where(
            Order.status == "delivered",
            Order.is_deleted == False,
        )
    )
    total_revenue = float(result.scalar_one())

    # Low stock count
    result = await db.execute(
        select(func.count(Product.id)).where(
            Product.stock <= Product.low_stock_threshold,
            Product.is_deleted == False,
        )
    )
    low_stock_count = result.scalar_one()

    return DashboardStats(
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        low_stock_count=low_stock_count,
    )


# ── Get low stock products ─────────────────────────────────────────────────────
async def get_low_stock(db: AsyncSession, limit: int = 20) -> list[LowStockItem]:
    logger.info("Get low stock products")

    result = await db.execute(
        select(Product)
        .where(
            Product.stock <= Product.low_stock_threshold,
            Product.is_deleted == False,
        )
        .order_by(Product.stock.asc())
        .limit(limit)
    )
    products = result.scalars().all()

    return [
        LowStockItem(
            product_id=p.id,
            name=p.name,
            sku=p.sku,
            stock=p.stock,
            low_stock_threshold=p.low_stock_threshold,
        )
        for p in products
    ]


# ── Get recent orders ──────────────────────────────────────────────────────────
async def get_recent_orders(db: AsyncSession, limit: int = 10) -> list[RecentOrderItem]:
    logger.info("Get recent orders")

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.customer))
        .where(Order.is_deleted == False)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    orders = result.scalars().all()

    return [
        RecentOrderItem(
            order_id=o.id,
            order_number=o.order_number,
            customer_name=o.customer.name,
            grand_total=round(float(o.grand_total), 2),
            status=o.status,
            payment_status=o.payment_status,
        )
        for o in orders
    ]