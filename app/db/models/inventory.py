# 📁 app/db/models/inventory.py

import uuid
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, ForeignKey, DateTime, Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


# ── Warehouse Model ────────────────────────────────────────────────────────────
class Warehouse(Base):
    __tablename__ = "warehouses"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name        = Column(String(100), unique=True, nullable=False)
    location    = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    is_deleted  = Column(Boolean, default=False, nullable=False)

    # Relationships
    inventory_logs = relationship("InventoryLog", back_populates="warehouse")


# ── Inventory Log Model ────────────────────────────────────────────────────────
# movement_type: stock_in | stock_out | adjustment
class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no              = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)

    # Movement
    movement_type   = Column(String(20), nullable=False)    # stock_in | stock_out | adjustment
    quantity        = Column(Integer, nullable=False)
    previous_stock  = Column(Integer, nullable=False)
    current_stock   = Column(Integer, nullable=False)

    # Pricing
    unit_cost       = Column(Numeric(10, 2), nullable=True)  # for stock_in
    unit_price      = Column(Numeric(10, 2), nullable=True)  # for stock_out

    # Reference
    reference_type  = Column(String(50), nullable=True)     # purchase_order | sales_order | adjustment
    reference_id    = Column(String(100), nullable=True)    # PO-2026-001

    # Extra info
    supplier_name   = Column(String(255), nullable=True)    # for stock_in
    customer_name   = Column(String(255), nullable=True)    # for stock_out
    note            = Column(Text, nullable=True)
    movement_date   = Column(DateTime(timezone=True), nullable=True)

    is_deleted      = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    product_id      = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id    = Column(UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    performed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    product         = relationship("Product", backref="inventory_logs")
    warehouse       = relationship("Warehouse", back_populates="inventory_logs")
    performed_by    = relationship("User", backref="inventory_logs")