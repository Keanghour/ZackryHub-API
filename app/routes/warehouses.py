# 📁 app/routes/warehouses.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core import require_roles, get_current_user
from app.schemas.warehouse import (
    WarehouseCreateRequest, WarehouseCreateResponse,
    WarehouseUpdateRequest, WarehouseUpdateResponse,
    WarehouseDetailResponse, WarehouseDeleteResponse,
    WarehouseListResponse, WarehouseData,
)
from app.services.warehouse_service import (
    create_warehouse, get_all_warehouses,
    get_warehouse_by_id, update_warehouse, delete_warehouse,
)

router = APIRouter(prefix="/api/v1/warehouses", tags=["Warehouses"])


@router.post("", response_model=WarehouseCreateResponse, status_code=201, summary="Create warehouse (Admin only)")
async def create(
    payload: WarehouseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    warehouse = await create_warehouse(db, payload)
    return WarehouseCreateResponse(success=True, message="Warehouse created successfully", data=WarehouseData.model_validate(warehouse))


@router.get("", response_model=WarehouseListResponse, summary="Get all warehouses")
async def list_warehouses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouses = await get_all_warehouses(db)
    return WarehouseListResponse(success=True, data=[WarehouseData.model_validate(w) for w in warehouses])


@router.get("/{warehouse_id}", response_model=WarehouseDetailResponse, summary="Get warehouse by ID")
async def get_warehouse(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouse = await get_warehouse_by_id(db, str(warehouse_id))
    return WarehouseDetailResponse(success=True, data=WarehouseData.model_validate(warehouse))


@router.put("/{warehouse_id}", response_model=WarehouseUpdateResponse, summary="Update warehouse (Admin only)")
async def update(
    warehouse_id: UUID,
    payload: WarehouseUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    warehouse = await update_warehouse(db, str(warehouse_id), payload)
    return WarehouseUpdateResponse(success=True, message="Warehouse updated successfully", data=WarehouseData.model_validate(warehouse))


@router.delete("/{warehouse_id}", response_model=WarehouseDeleteResponse, summary="Delete warehouse (Admin only)")
async def delete(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    await delete_warehouse(db, str(warehouse_id))
    return WarehouseDeleteResponse(success=True, message="Warehouse deleted successfully")