# 📁 app/db/models/user.py

import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Table, Text, DateTime, Integer, Identity
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


# ── Many-to-Many: Role <-> Permission ─────────────────────────────────────────
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# ── Many-to-Many: User <-> Role ────────────────────────────────────────────────
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


# ── Permission Model ───────────────────────────────────────────────────────────
class Permission(Base):
    __tablename__ = "permissions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_deleted  = Column(Boolean, default=False, nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# ── Role Model ─────────────────────────────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no          = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name        = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_deleted  = Column(Boolean, default=False, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users       = relationship("User", secondary=user_roles, back_populates="roles")


# ── User Model ─────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    no            = Column(Integer, Identity(start=1, cycle=False), nullable=False, unique=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=True, nullable=False)
    is_verified   = Column(Boolean, default=False, nullable=False)
    is_deleted    = Column(Boolean, default=False, nullable=False)

    roles          = relationship("Role", secondary=user_roles, back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


# ── Refresh Token Model ────────────────────────────────────────────────────────
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token      = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


# ── Password Reset Token Model ─────────────────────────────────────────────────
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token      = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used    = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    user = relationship("User", backref="password_reset_tokens")