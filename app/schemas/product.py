# 📁 app/schemas/product.py

from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Category schema ────────────────────────────────────────────────────────────
class CategoryItem(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


# ── Create Product ─────────────────────────────────────────────────────────────
class ProductCreateRequest(BaseModel):
    name:        str            = Field(..., min_length=1, max_length=255, example="iPhone 15")
    brand:       Optional[str]  = Field(None, max_length=100, example="Apple")
    sku:         str            = Field(..., min_length=1, max_length=100, example="IPH15-001")
    barcode:     Optional[str]  = Field(None, max_length=100, example="885909950805")
    description: Optional[str]  = Field(None, example="Apple iPhone 15 128GB")
    image_url:   Optional[str]  = Field(None, max_length=500, example="https://cdn.com/iphone15.jpg")
    price:       float          = Field(..., gt=0, example=1200.00)
    cost_price:  Optional[float] = Field(None, ge=0, example=1000.00)
    stock:       int            = Field(0, ge=0, example=50)
    low_stock_threshold: int    = Field(10, ge=0, example=10)
    category_id: Optional[UUID] = Field(None)
    status:      str            = Field("active", example="active")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "inactive", "out_of_stock"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


# ── Update Product ─────────────────────────────────────────────────────────────
class ProductUpdateRequest(BaseModel):
    name:        Optional[str]   = Field(None, min_length=1, max_length=255)
    brand:       Optional[str]   = Field(None, max_length=100)
    sku:         Optional[str]   = Field(None, min_length=1, max_length=100)
    barcode:     Optional[str]   = Field(None, max_length=100)
    description: Optional[str]   = None
    image_url:   Optional[str]   = Field(None, max_length=500)
    price:       Optional[float] = Field(None, gt=0)
    cost_price:  Optional[float] = Field(None, ge=0)
    stock:       Optional[int]   = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    category_id: Optional[UUID]  = None
    status:      Optional[str]   = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v is None:
            return v
        allowed = {"active", "inactive", "out_of_stock"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


# ── Product response data ──────────────────────────────────────────────────────
class ProductData(BaseModel):
    id:          UUID
    no:          int
    name:        str
    brand:       Optional[str]  = None
    sku:         str
    barcode:     Optional[str]  = None
    description: Optional[str]  = None
    image_url:   Optional[str]  = None
    price:       float
    cost_price:  Optional[float] = None
    stock:       int
    low_stock_threshold: int
    status:      str
    category:    Optional[CategoryItem] = None
    created_at:  datetime

    class Config:
        from_attributes = True

    # ✅ Serialize Decimal from DB → clean float in response
    @field_serializer("price", "cost_price")
    def serialize_price(self, v) -> Optional[float]:
        if v is None:
            return None
        return round(float(v), 2)


# ── Responses ──────────────────────────────────────────────────────────────────
class ProductCreateResponse(BaseModel):
    success: bool = True
    message: str  = "Product created successfully"
    data: ProductData


class ProductUpdateResponse(BaseModel):
    success: bool = True
    message: str  = "Product updated successfully"
    data: ProductData


class ProductDetailResponse(BaseModel):
    success: bool = True
    data: ProductData


class ProductDeleteResponse(BaseModel):
    success: bool = True
    message: str  = "Product deleted successfully"