# 📁 app/db/models/product.py

import uuid
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


# ── Category Model ─────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_deleted  = Column(Boolean, default=False, nullable=False)

    products = relationship("Product", back_populates="category")


# ── Product Model ──────────────────────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name        = Column(String(255), nullable=False, index=True)
    brand       = Column(String(100), nullable=True)
    sku         = Column(String(100), unique=True, nullable=False, index=True)
    barcode     = Column(String(100), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    image_url   = Column(String(500), nullable=True)
    price       = Column(Numeric(10, 2), nullable=False)
    cost_price  = Column(Numeric(10, 2), nullable=True)
    stock                = Column(Integer, default=0, nullable=False)
    low_stock_threshold  = Column(Integer, default=10, nullable=False)
    status      = Column(String(20), default="active", nullable=False)
    is_deleted  = Column(Boolean, default=False, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    category    = relationship("Category", back_populates="products")