# 📁 app/services/inventory_service.py

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.inventory import InventoryLog, Warehouse
from app.db.models.product import Product
from app.db.models.user import User
from app.schemas.inventory import StockInRequest, StockOutRequest, StockAdjustRequest
from app.schemas.inventory import InventoryLogData, ProductRef, WarehouseRef, ReferenceData, PerformedByRef
from app.utils.pagination import PaginationParams, PaginationMeta
from app.core import logger, InsufficientStockException


# ── Helper: load log with relations ───────────────────────────────────────────
async def _load_log(db: AsyncSession, log_id) -> InventoryLog:
    result = await db.execute(
        select(InventoryLog)
        .options(
            selectinload(InventoryLog.product),
            selectinload(InventoryLog.warehouse),
            selectinload(InventoryLog.performed_by),
        )
        .where(InventoryLog.id == log_id)
    )
    return result.scalar_one()


# ── Helper: build InventoryLogData from ORM ───────────────────────────────────
def to_log_data(log: InventoryLog) -> InventoryLogData:
    unit_cost  = float(log.unit_cost)  if log.unit_cost  else None
    unit_price = float(log.unit_price) if log.unit_price else None

    return InventoryLogData(
        transaction_id=log.id,
        movement_type=log.movement_type,
        product=ProductRef(
            id=log.product.id,
            sku=log.product.sku,
            barcode=log.product.barcode,
            name=log.product.name,
        ),
        warehouse=WarehouseRef(id=log.warehouse.id, name=log.warehouse.name),
        quantity=log.quantity,
        previous_stock=log.previous_stock,
        current_stock=log.current_stock,
        unit_cost=unit_cost,
        total_cost=round(unit_cost * log.quantity, 2) if unit_cost else None,
        unit_price=unit_price,
        total_amount=round(unit_price * log.quantity, 2) if unit_price else None,
        movement_date=log.movement_date,
        reference=ReferenceData(type=log.reference_type, id=log.reference_id),
        supplier_name=log.supplier_name,
        customer_name=log.customer_name,
        note=log.note,
        performed_by=PerformedByRef(
            id=log.performed_by.id,
            name=log.performed_by.name,
        ) if log.performed_by else None,
        created_at=log.created_at,
    )


# ── Stock In ───────────────────────────────────────────────────────────────────
async def stock_in(db: AsyncSession, payload: StockInRequest, current_user: User) -> InventoryLogData:
    logger.info(f"Stock in | product_id={payload.product_id} qty={payload.quantity} user={current_user.id}")

    # Validate product
    result = await db.execute(
        select(Product).where(Product.id == payload.product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate warehouse
    result = await db.execute(
        select(Warehouse).where(
            Warehouse.id == payload.warehouse_id,
            Warehouse.is_deleted == False,
            Warehouse.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found or inactive")

    previous_stock = product.stock
    product.stock += payload.quantity
    current_stock  = product.stock

    # Auto update status
    if product.stock > 0 and product.status == "out_of_stock":
        product.status = "active"

    log = InventoryLog(
        movement_type   = "stock_in",
        product_id      = payload.product_id,
        warehouse_id    = payload.warehouse_id,
        quantity        = payload.quantity,
        previous_stock  = previous_stock,
        current_stock   = current_stock,
        unit_cost       = payload.unit_cost,
        reference_type  = payload.reference_type,
        reference_id    = payload.reference_id,
        supplier_name   = payload.supplier_name,
        note            = payload.note,
        movement_date   = payload.stock_in_date or datetime.now(timezone.utc),
        performed_by_id = current_user.id,
    )
    db.add(log)
    await db.flush()

    log = await _load_log(db, log.id)
    logger.info(f"Stock in success | product={product.sku} prev={previous_stock} curr={current_stock}")
    return to_log_data(log)


# ── Stock Out ──────────────────────────────────────────────────────────────────
async def stock_out(db: AsyncSession, payload: StockOutRequest, current_user: User) -> InventoryLogData:
    logger.info(f"Stock out | product_id={payload.product_id} qty={payload.quantity} user={current_user.id}")

    # Validate product
    result = await db.execute(
        select(Product).where(Product.id == payload.product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # ✅ Check sufficient stock — clean 400 error
    if product.stock < payload.quantity:
        raise InsufficientStockException(
            available_stock=product.stock,
            requested_quantity=payload.quantity,
        )

    # Validate warehouse
    result = await db.execute(
        select(Warehouse).where(
            Warehouse.id == payload.warehouse_id,
            Warehouse.is_deleted == False,
            Warehouse.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found or inactive")

    previous_stock = product.stock
    product.stock -= payload.quantity
    current_stock  = product.stock

    # Auto update status if out of stock
    if product.stock == 0:
        product.status = "out_of_stock"

    log = InventoryLog(
        movement_type   = "stock_out",
        product_id      = payload.product_id,
        warehouse_id    = payload.warehouse_id,
        quantity        = payload.quantity,
        previous_stock  = previous_stock,
        current_stock   = current_stock,
        unit_price      = payload.unit_price,
        reference_type  = payload.reference_type,
        reference_id    = payload.reference_id,
        customer_name   = payload.customer_name,
        note            = payload.note,
        movement_date   = payload.stock_out_date or datetime.now(timezone.utc),
        performed_by_id = current_user.id,
    )
    db.add(log)
    await db.flush()

    log = await _load_log(db, log.id)
    logger.info(f"Stock out success | product={product.sku} prev={previous_stock} curr={current_stock}")
    return to_log_data(log)


# ── Stock Adjustment ───────────────────────────────────────────────────────────
async def stock_adjust(db: AsyncSession, payload: StockAdjustRequest, current_user: User) -> InventoryLogData:
    logger.info(f"Stock adjust | product_id={payload.product_id} new_qty={payload.new_quantity} user={current_user.id}")

    result = await db.execute(
        select(Product).where(Product.id == payload.product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    result = await db.execute(
        select(Warehouse).where(
            Warehouse.id == payload.warehouse_id,
            Warehouse.is_deleted == False,
            Warehouse.is_active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found or inactive")

    previous_stock = product.stock
    diff           = payload.new_quantity - previous_stock
    product.stock  = payload.new_quantity
    current_stock  = product.stock

    # Auto update status
    if product.stock == 0:
        product.status = "out_of_stock"
    elif product.stock > 0 and product.status == "out_of_stock":
        product.status = "active"

    log = InventoryLog(
        movement_type   = "adjustment",
        product_id      = payload.product_id,
        warehouse_id    = payload.warehouse_id,
        quantity        = abs(diff),
        previous_stock  = previous_stock,
        current_stock   = current_stock,
        note            = payload.note,
        reference_type  = "adjustment",
        movement_date   = datetime.now(timezone.utc),
        performed_by_id = current_user.id,
    )
    db.add(log)
    await db.flush()

    log = await _load_log(db, log.id)
    logger.info(f"Stock adjust success | product={product.sku} prev={previous_stock} curr={current_stock}")
    return to_log_data(log)


# ── Get inventory logs ─────────────────────────────────────────────────────────
async def get_inventory_logs(
    db: AsyncSession,
    params: PaginationParams,
    product_id: str = None,
    warehouse_id: str = None,
    movement_type: str = None,
) -> tuple[list[InventoryLog], PaginationMeta]:

    query = (
        select(InventoryLog)
        .options(
            selectinload(InventoryLog.product),
            selectinload(InventoryLog.warehouse),
            selectinload(InventoryLog.performed_by),
        )
        .where(InventoryLog.is_deleted == False)
    )

    if product_id:
        query = query.where(InventoryLog.product_id == product_id)
    if warehouse_id:
        query = query.where(InventoryLog.warehouse_id == warehouse_id)
    if movement_type:
        query = query.where(InventoryLog.movement_type == movement_type)
    if params.search:
        kw = f"%{params.search}%"
        query = query.join(InventoryLog.product).where(
            or_(Product.name.ilike(kw), Product.sku.ilike(kw))
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(InventoryLog.created_at.desc()).offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    logs = list(result.scalars().all())

    total_pages = (total + params.limit - 1) // params.limit
    meta = PaginationMeta(total=total, page=params.page, limit=params.limit, total_pages=total_pages)
    return logs, meta