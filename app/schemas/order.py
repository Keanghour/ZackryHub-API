# 📁 app/schemas/order.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ── Nested refs ────────────────────────────────────────────────────────────────
class CustomerRef(BaseModel):
    id:   UUID
    name: str
    class Config:
        from_attributes = True


class WarehouseRef(BaseModel):
    id:   UUID
    name: str
    class Config:
        from_attributes = True


class OrderItemRequest(BaseModel):
    product_id: UUID  = Field(..., example="uuid-product")
    quantity:   int   = Field(..., gt=0, example=2)


class OrderItemData(BaseModel):
    product_id:   UUID
    product_name: str
    sku:          str
    quantity:     int
    unit_price:   float
    line_total:   float

    @field_serializer("unit_price", "line_total")
    def serialize_float(self, v) -> float:
        return round(float(v), 2)


# ── Create Order ───────────────────────────────────────────────────────────────
class OrderCreateRequest(BaseModel):
    customer_id:      UUID              = Field(..., example="uuid-customer")
    warehouse_id:     UUID              = Field(..., example="uuid-warehouse")
    items:            List[OrderItemRequest] = Field(..., min_length=1)
    order_date:       Optional[datetime] = Field(None, example="2026-06-01T10:00:00Z")
    currency:         str               = Field("USD", example="USD")
    tax_percent:      float             = Field(0, ge=0, le=100, example=7.0)
    discount_percent: float             = Field(0, ge=0, le=100, example=5.0)
    note:             Optional[str]     = Field(None, example="Customer requested fast delivery")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError("Order must have at least one item")
        # Check duplicate product_id
        ids = [str(i.product_id) for i in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate products in order items")
        return v


# ── Update Order Status ────────────────────────────────────────────────────────
class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., example="confirmed")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


# ── Update Payment Status ──────────────────────────────────────────────────────
class PaymentStatusUpdateRequest(BaseModel):
    payment_status: str = Field(..., example="paid")

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, v: str) -> str:
        allowed = {"unpaid", "partial", "paid", "refunded"}
        if v not in allowed:
            raise ValueError(f"Payment status must be one of: {', '.join(allowed)}")
        return v


# ── Order response data ────────────────────────────────────────────────────────
class OrderData(BaseModel):
    order_id:         UUID
    order_number:     str
    customer:         CustomerRef
    warehouse:        WarehouseRef
    items:            List[OrderItemData]
    currency:         str
    subtotal:         float
    tax_percent:      float
    tax_amount:       float
    discount_percent: float
    discount_amount:  float
    grand_total:      float
    status:           str
    payment_status:   str
    order_date:       Optional[datetime] = None
    note:             Optional[str]      = None
    created_at:       datetime

    @field_serializer("subtotal", "tax_percent", "tax_amount", "discount_percent", "discount_amount", "grand_total")
    def serialize_float(self, v) -> float:
        return round(float(v), 2)


# ── Responses ──────────────────────────────────────────────────────────────────
class OrderCreateResponse(BaseModel):
    success: bool = True
    message: str  = "Order created successfully"
    data: OrderData


class OrderDetailResponse(BaseModel):
    success: bool = True
    data: OrderData


class OrderStatusResponse(BaseModel):
    success: bool = True
    message: str
    data: OrderData


class OrderCancelResponse(BaseModel):
    success: bool = True
    message: str  = "Order cancelled successfully"
    data: OrderData