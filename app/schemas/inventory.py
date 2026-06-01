# 📁 app/schemas/inventory.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Nested objects in response ─────────────────────────────────────────────────
class ProductRef(BaseModel):
    id:      UUID
    sku:     str
    barcode: Optional[str] = None
    name:    str

    class Config:
        from_attributes = True


class WarehouseRef(BaseModel):
    id:   UUID
    name: str

    class Config:
        from_attributes = True


class ReferenceData(BaseModel):
    type: Optional[str] = None
    id:   Optional[str] = None


class PerformedByRef(BaseModel):
    id:   UUID
    name: str

    class Config:
        from_attributes = True


# ── Stock In ───────────────────────────────────────────────────────────────────
class StockInRequest(BaseModel):
    product_id:     UUID           = Field(..., example="uuid-product")
    warehouse_id:   UUID           = Field(..., example="uuid-warehouse")
    quantity:       int            = Field(..., gt=0, example=20)
    stock_in_date:  Optional[datetime] = Field(None, example="2026-05-25T10:00:00Z")
    reference_type: Optional[str]  = Field(None, example="purchase_order")
    reference_id:   Optional[str]  = Field(None, example="PO-2026-001")
    supplier_name:  Optional[str]  = Field(None, example="Apple Supplier Ltd")
    unit_cost:      Optional[float] = Field(None, ge=0, example=1200.50)
    note:           Optional[str]  = Field(None, example="New stock arrival")

    @field_validator("reference_type")
    @classmethod
    def validate_reference_type(cls, v):
        if v is None:
            return v
        allowed = {"purchase_order", "transfer", "return", "adjustment", "opening_stock"}
        if v not in allowed:
            raise ValueError(f"reference_type must be one of: {', '.join(allowed)}")
        return v


# ── Stock Out ──────────────────────────────────────────────────────────────────
class StockOutRequest(BaseModel):
    product_id:      UUID           = Field(..., example="uuid-product")
    warehouse_id:    UUID           = Field(..., example="uuid-warehouse")
    quantity:        int            = Field(..., gt=0, example=5)
    stock_out_date:  Optional[datetime] = Field(None, example="2026-05-29T14:00:00Z")
    reference_type:  Optional[str]  = Field(None, example="sales_order")
    reference_id:    Optional[str]  = Field(None, example="SO-2026-101")
    customer_name:   Optional[str]  = Field(None, example="John Doe")
    unit_price:      Optional[float] = Field(None, ge=0, example=1500.00)
    note:            Optional[str]  = Field(None, example="Sold to customer")

    @field_validator("reference_type")
    @classmethod
    def validate_reference_type(cls, v):
        if v is None:
            return v
        allowed = {"sales_order", "transfer", "damage", "expired", "adjustment"}
        if v not in allowed:
            raise ValueError(f"reference_type must be one of: {', '.join(allowed)}")
        return v


# ── Stock Adjustment ───────────────────────────────────────────────────────────
class StockAdjustRequest(BaseModel):
    product_id:   UUID  = Field(..., example="uuid-product")
    warehouse_id: UUID  = Field(..., example="uuid-warehouse")
    new_quantity: int   = Field(..., ge=0, example=45)
    note:         str   = Field(..., min_length=1, example="Physical count correction")


# ── Inventory log response data ────────────────────────────────────────────────
class InventoryLogData(BaseModel):
    transaction_id:  UUID
    movement_type:   str
    product:         ProductRef
    warehouse:       WarehouseRef
    quantity:        int
    previous_stock:  int
    current_stock:   int
    unit_cost:       Optional[float] = None
    total_cost:      Optional[float] = None
    unit_price:      Optional[float] = None
    total_amount:    Optional[float] = None
    movement_date:   Optional[datetime] = None
    reference:       ReferenceData
    supplier_name:   Optional[str] = None
    customer_name:   Optional[str] = None
    note:            Optional[str] = None
    performed_by:    Optional[PerformedByRef] = None
    created_at:      datetime

    class Config:
        from_attributes = True

    @field_serializer("unit_cost", "total_cost", "unit_price", "total_amount")
    def serialize_float(self, v) -> Optional[float]:
        if v is None:
            return None
        return round(float(v), 2)


# ── Responses ──────────────────────────────────────────────────────────────────
class StockInResponse(BaseModel):
    success: bool = True
    message: str  = "Stock added successfully"
    data: InventoryLogData


class StockOutResponse(BaseModel):
    success: bool = True
    message: str  = "Stock removed successfully"
    data: InventoryLogData


class StockAdjustResponse(BaseModel):
    success: bool = True
    message: str  = "Stock adjusted successfully"
    data: InventoryLogData