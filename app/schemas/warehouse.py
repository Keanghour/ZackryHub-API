# 📁 app/schemas/warehouse.py

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseResponse


class WarehouseCreateRequest(BaseModel):
    name:        str           = Field(..., min_length=1, max_length=100, example="Main Warehouse")
    location:    Optional[str] = Field(None, max_length=255, example="Bangkok, Thailand")
    description: Optional[str] = Field(None, max_length=255)


class WarehouseUpdateRequest(BaseModel):
    name:        Optional[str]  = Field(None, min_length=1, max_length=100)
    location:    Optional[str]  = Field(None, max_length=255)
    description: Optional[str]  = Field(None, max_length=255)
    is_active:   Optional[bool] = None


class WarehouseData(BaseModel):
    id:          UUID
    no:          int
    name:        str
    location:    Optional[str] = None
    description: Optional[str] = None
    is_active:   bool
    created_at:  datetime
    class Config:
        from_attributes = True


class WarehouseCreateResponse(BaseResponse):
    code:    int  = 201
    message: str  = "Warehouse created successfully"
    data: WarehouseData


class WarehouseUpdateResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Warehouse updated successfully"
    data: WarehouseData


class WarehouseDetailResponse(BaseResponse):
    code:    int  = 200
    data: WarehouseData


class WarehouseDeleteResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Warehouse deleted successfully"


class WarehouseListResponse(BaseResponse):
    code:    int  = 200
    data: List[WarehouseData]