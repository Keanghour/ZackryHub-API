# 📁 app/schemas/dashboard.py

from pydantic import BaseModel
from typing import List
from uuid import UUID
from app.schemas.base import BaseResponse


class DashboardStats(BaseModel):
    total_users:      int
    total_products:   int
    total_orders:     int
    total_revenue:    float
    pending_orders:   int
    confirmed_orders: int
    low_stock_count:  int


class StatsResponse(BaseResponse):
    code:    int  = 200
    data: DashboardStats


class LowStockItem(BaseModel):
    product_id:          UUID
    name:                str
    sku:                 str
    stock:               int
    low_stock_threshold: int


class LowStockResponse(BaseResponse):
    code:    int  = 200
    data: List[LowStockItem]


class RecentOrderItem(BaseModel):
    order_id:       UUID
    order_number:   str
    customer_name:  str
    grand_total:    float
    status:         str
    payment_status: str


class RecentOrdersResponse(BaseResponse):
    code:    int  = 200
    data: List[RecentOrderItem]