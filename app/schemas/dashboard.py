# 📁 app/schemas/dashboard.py

from pydantic import BaseModel
from typing import Optional
from uuid import UUID


# ── Stats ──────────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_users:     int
    total_products:  int
    total_orders:    int
    total_revenue:   float
    pending_orders:  int
    confirmed_orders: int
    low_stock_count: int


class StatsResponse(BaseModel):
    success: bool = True
    data: DashboardStats


# ── Low stock ──────────────────────────────────────────────────────────────────
class LowStockItem(BaseModel):
    product_id:          UUID
    name:                str
    sku:                 str
    stock:               int
    low_stock_threshold: int


class LowStockResponse(BaseModel):
    success: bool = True
    data: list[LowStockItem]


# ── Recent orders ──────────────────────────────────────────────────────────────
class RecentOrderItem(BaseModel):
    order_id:      UUID
    order_number:  str
    customer_name: str
    grand_total:   float
    status:        str
    payment_status: str


class RecentOrdersResponse(BaseModel):
    success: bool = True
    data: list[RecentOrderItem]