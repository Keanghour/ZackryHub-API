# 📁 app/services/order_service.py

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product
from app.db.models.user import User
from app.db.models.inventory import Warehouse, InventoryLog
from app.schemas.order import (
    OrderCreateRequest, OrderData, OrderItemData,
    CustomerRef, WarehouseRef,
)
from app.utils.pagination import PaginationParams, PaginationMeta
from app.core import logger, InsufficientStockException


# ── Helper: generate order number SO-2026-0001 ─────────────────────────────────
async def _generate_order_number(db: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    result = await db.execute(
        select(func.count(Order.id)).where(
            Order.order_number.like(f"SO-{year}-%")
        )
    )
    count = result.scalar_one() + 1
    return f"SO-{year}-{str(count).zfill(4)}"


# ── Helper: load order with all relations ──────────────────────────────────────
async def _load_order(db: AsyncSession, order_id) -> Order:
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.warehouse),
            selectinload(Order.created_by),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .where(Order.id == order_id)
    )
    return result.scalar_one()


# ── Helper: build OrderData from ORM ──────────────────────────────────────────
def to_order_data(order: Order) -> OrderData:
    return OrderData(
        order_id=order.id,
        order_number=order.order_number,
        customer=CustomerRef(id=order.customer.id, name=order.customer.name),
        warehouse=WarehouseRef(id=order.warehouse.id, name=order.warehouse.name),
        items=[
            OrderItemData(
                product_id=item.product_id,
                product_name=item.product.name,
                sku=item.product.sku,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                line_total=float(item.line_total),
            )
            for item in order.items if not item.is_deleted
        ],
        currency=order.currency,
        subtotal=float(order.subtotal),
        tax_percent=float(order.tax_percent),
        tax_amount=float(order.tax_amount),
        discount_percent=float(order.discount_percent),
        discount_amount=float(order.discount_amount),
        grand_total=float(order.grand_total),
        status=order.status,
        payment_status=order.payment_status,
        order_date=order.order_date,
        note=order.note,
        created_at=order.created_at,
    )


# ── Create Order ───────────────────────────────────────────────────────────────
async def create_order(db: AsyncSession, payload: OrderCreateRequest, current_user: User) -> OrderData:
    logger.info(f"Create order | customer_id={payload.customer_id} items={len(payload.items)} user={current_user.id}")

    # Validate customer exists and has customer role
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == payload.customer_id, User.is_deleted == False, User.is_active == True)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

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

    # Validate all products and calculate subtotal
    order_items = []
    subtotal = 0.0

    for item_req in payload.items:
        result = await db.execute(
            select(Product).where(
                Product.id == item_req.product_id,
                Product.is_deleted == False,
                Product.status == "active",
            )
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_req.product_id} not found or inactive",
            )

        unit_price = float(product.price)
        line_total = round(unit_price * item_req.quantity, 2)
        subtotal  += line_total

        order_items.append({
            "product_id": item_req.product_id,
            "quantity":   item_req.quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    # Calculate tax, discount, grand total
    subtotal         = round(subtotal, 2)
    tax_amount       = round(subtotal * float(payload.tax_percent) / 100, 2)
    discount_amount  = round(subtotal * float(payload.discount_percent) / 100, 2)
    grand_total      = round(subtotal + tax_amount - discount_amount, 2)

    # Generate order number
    order_number = await _generate_order_number(db)

    # Create order
    order = Order(
        order_number     = order_number,
        customer_id      = payload.customer_id,
        warehouse_id     = payload.warehouse_id,
        created_by_id    = current_user.id,
        currency         = payload.currency,
        subtotal         = subtotal,
        tax_percent      = payload.tax_percent,
        tax_amount       = tax_amount,
        discount_percent = payload.discount_percent,
        discount_amount  = discount_amount,
        grand_total      = grand_total,
        status           = "pending",
        payment_status   = "unpaid",
        order_date       = payload.order_date or datetime.now(timezone.utc),
        note             = payload.note,
    )
    db.add(order)
    await db.flush()

    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id   = order.id,
            product_id = item_data["product_id"],
            quantity   = item_data["quantity"],
            unit_price = item_data["unit_price"],
            line_total = item_data["line_total"],
        )
        db.add(order_item)

    await db.flush()

    order = await _load_order(db, order.id)
    logger.info(f"Order created | order_number={order.order_number} grand_total={grand_total}")
    return to_order_data(order)


# ── Update Order Status ────────────────────────────────────────────────────────
async def update_order_status(
    db: AsyncSession,
    order_id: str,
    new_status: str,
    current_user: User,
) -> OrderData:
    logger.info(f"Update order status | order_id={order_id} new_status={new_status}")

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id, Order.is_deleted == False)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # ── Status transition rules ────────────────────────────────────────────────
    allowed_transitions = {
        "pending":   ["confirmed", "cancelled"],
        "confirmed": ["shipped",   "cancelled"],
        "shipped":   ["delivered"],
        "delivered": [],
        "cancelled": [],
    }

    if new_status not in allowed_transitions.get(order.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change status from '{order.status}' to '{new_status}'",
        )

    # ── Deduct stock when confirmed ────────────────────────────────────────────
    if new_status == "confirmed":
        for item in order.items:
            if item.is_deleted:
                continue
            product = item.product

            # Check sufficient stock
            if product.stock < item.quantity:
                raise InsufficientStockException(
                    available_stock=product.stock,
                    requested_quantity=item.quantity,
                )

            prev_stock    = product.stock
            product.stock -= item.quantity

            # Auto update product status
            if product.stock == 0:
                product.status = "out_of_stock"

            # Log inventory movement
            inv_log = InventoryLog(
                movement_type   = "stock_out",
                product_id      = product.id,
                warehouse_id    = order.warehouse_id,
                quantity        = item.quantity,
                previous_stock  = prev_stock,
                current_stock   = product.stock,
                unit_price      = item.unit_price,
                reference_type  = "sales_order",
                reference_id    = order.order_number,
                note            = f"Order confirmed: {order.order_number}",
                movement_date   = datetime.now(timezone.utc),
                performed_by_id = current_user.id,
            )
            db.add(inv_log)

    # ── Restore stock when cancelled from confirmed ────────────────────────────
    if new_status == "cancelled" and order.status == "confirmed":
        for item in order.items:
            if item.is_deleted:
                continue
            product = item.product
            prev_stock    = product.stock
            product.stock += item.quantity

            if product.stock > 0 and product.status == "out_of_stock":
                product.status = "active"

            inv_log = InventoryLog(
                movement_type   = "stock_in",
                product_id      = product.id,
                warehouse_id    = order.warehouse_id,
                quantity        = item.quantity,
                previous_stock  = prev_stock,
                current_stock   = product.stock,
                reference_type  = "return",
                reference_id    = order.order_number,
                note            = f"Order cancelled: {order.order_number}",
                movement_date   = datetime.now(timezone.utc),
                performed_by_id = current_user.id,
            )
            db.add(inv_log)

    order.status = new_status
    await db.flush()

    order = await _load_order(db, order.id)
    logger.info(f"Order status updated | order_number={order.order_number} status={new_status}")
    return to_order_data(order)


# ── Update Payment Status ──────────────────────────────────────────────────────
async def update_payment_status(
    db: AsyncSession,
    order_id: str,
    payment_status: str,
) -> OrderData:
    logger.info(f"Update payment status | order_id={order_id} payment_status={payment_status}")

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.is_deleted == False)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update payment status of a cancelled order",
        )

    order.payment_status = payment_status
    await db.flush()

    order = await _load_order(db, order.id)
    return to_order_data(order)


# ── Get order by ID ────────────────────────────────────────────────────────────
async def get_order_by_id(db: AsyncSession, order_id: str) -> OrderData:
    order = await _load_order(db, order_id)
    if not order or order.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return to_order_data(order)


# ── Get all orders with pagination ─────────────────────────────────────────────
async def get_orders(
    db: AsyncSession,
    params: PaginationParams,
    status: str = None,
    payment_status: str = None,
    customer_id: str = None,
    warehouse_id: str = None,
) -> tuple[list[OrderData], PaginationMeta]:

    query = (
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.warehouse),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .where(Order.is_deleted == False)
    )

    if status:
        query = query.where(Order.status == status)
    if payment_status:
        query = query.where(Order.payment_status == payment_status)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    if warehouse_id:
        query = query.where(Order.warehouse_id == warehouse_id)
    if params.search:
        query = query.where(Order.order_number.ilike(f"%{params.search}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Order.created_at.desc()).offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    orders = list(result.scalars().all())

    total_pages = (total + params.limit - 1) // params.limit
    meta = PaginationMeta(total=total, page=params.page, limit=params.limit, total_pages=total_pages)

    return [to_order_data(o) for o in orders], meta