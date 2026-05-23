# 📁 app/schemas/role.py

from pydantic import BaseModel
from uuid import UUID
from typing import List


class PermissionItem(BaseModel):
    id: UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class RoleItem(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    permissions: List[PermissionItem] = []

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    success: bool = True
    data: List[RoleItem]


class RoleDetailResponse(BaseModel):
    success: bool = True
    data: RoleItem


# ── Assign / Remove role ───────────────────────────────────────────────────────

class AssignRoleRequest(BaseModel):
    role_name: str


class AssignRoleResponse(BaseModel):
    success: bool = True
    message: str
    data: List[dict] = []


class RemoveRoleRequest(BaseModel):
    role_name: str


class RemoveRoleResponse(BaseModel):
    success: bool = True
    message: str


# ── User roles ─────────────────────────────────────────────────────────────────

class UserRolesResponse(BaseModel):
    success: bool = True
    data: List[RoleItem]