# 📁 app/db/models/order.py

import uuid
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, ForeignKey, DateTime, Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no               = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    order_number     = Column(String(50), unique=True, nullable=False, index=True)

    customer_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id     = Column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    currency         = Column(String(10), default="USD", nullable=False)
    subtotal         = Column(Numeric(12, 2), default=0, nullable=False)
    tax_percent      = Column(Numeric(5, 2), default=0, nullable=False)
    tax_amount       = Column(Numeric(12, 2), default=0, nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)
    discount_amount  = Column(Numeric(12, 2), default=0, nullable=False)
    grand_total      = Column(Numeric(12, 2), default=0, nullable=False)

    status           = Column(String(20), default="pending", nullable=False)
    payment_status   = Column(String(20), default="unpaid", nullable=False)

    order_date       = Column(DateTime(timezone=True), nullable=True)
    note             = Column(Text, nullable=True)
    is_deleted       = Column(Boolean, default=False, nullable=False)

    customer         = relationship("User", foreign_keys=[customer_id], backref="orders_as_customer")
    created_by       = relationship("User", foreign_keys=[created_by_id], backref="orders_created")
    warehouse        = relationship("Warehouse", backref="orders")
    items            = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    order_id    = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id  = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity    = Column(Integer, nullable=False)
    unit_price  = Column(Numeric(10, 2), nullable=False)
    line_total  = Column(Numeric(12, 2), nullable=False)
    is_deleted  = Column(Boolean, default=False, nullable=False)

    order       = relationship("Order", back_populates="items")
    product     = relationship("Product", backref="order_items")