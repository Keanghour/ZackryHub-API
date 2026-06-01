# 📁 app/services/warehouse_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.db.models.inventory import Warehouse
from app.schemas.warehouse import WarehouseCreateRequest, WarehouseUpdateRequest
from app.core import logger


async def create_warehouse(db: AsyncSession, payload: WarehouseCreateRequest) -> Warehouse:
    logger.info(f"Create warehouse | name={payload.name}")

    result = await db.execute(
        select(Warehouse).where(
            func.lower(Warehouse.name) == payload.name.lower().strip(),
            Warehouse.is_deleted == False,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Warehouse '{payload.name}' already exists")

    warehouse = Warehouse(
        name=payload.name.strip(),
        location=payload.location,
        description=payload.description,
    )
    db.add(warehouse)
    await db.flush()
    await db.refresh(warehouse)

    logger.info(f"Warehouse created | id={warehouse.id}")
    return warehouse


async def get_all_warehouses(db: AsyncSession) -> list[Warehouse]:
    result = await db.execute(
        select(Warehouse)
        .where(Warehouse.is_deleted == False)
        .order_by(Warehouse.name.asc())
    )
    return list(result.scalars().all())


async def get_warehouse_by_id(db: AsyncSession, warehouse_id: str) -> Warehouse:
    result = await db.execute(
        select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.is_deleted == False)
    )
    warehouse = result.scalar_one_or_none()
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return warehouse


async def update_warehouse(db: AsyncSession, warehouse_id: str, payload: WarehouseUpdateRequest) -> Warehouse:
    warehouse = await get_warehouse_by_id(db, warehouse_id)

    if payload.name and payload.name.strip().lower() != warehouse.name.lower():
        result = await db.execute(
            select(Warehouse).where(
                func.lower(Warehouse.name) == payload.name.lower().strip(),
                Warehouse.is_deleted == False,
                Warehouse.id != warehouse.id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Warehouse '{payload.name}' already exists")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(warehouse, field, value)

    await db.flush()
    await db.refresh(warehouse)
    logger.info(f"Warehouse updated | id={warehouse.id}")
    return warehouse


async def delete_warehouse(db: AsyncSession, warehouse_id: str) -> None:
    warehouse = await get_warehouse_by_id(db, warehouse_id)
    warehouse.is_deleted = True
    await db.flush()
    logger.info(f"Warehouse deleted | id={warehouse_id}")