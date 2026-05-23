# 📁 app/schemas/user.py

from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime


# ── Role inside user ───────────────────────────────────────────────────────────
class UserRoleData(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


# ── User item in list ──────────────────────────────────────────────────────────
class UserListItem(BaseModel):
    id: UUID
    name: str
    email: str
    is_active: bool
    is_verified: bool
    roles: List[UserRoleData] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ── Assign Role ────────────────────────────────────────────────────────────────
class AssignRoleRequest(BaseModel):
    role_name: str


class AssignRoleResponse(BaseModel):
    success: bool = True
    message: str = "Role assigned successfully"
    data: UserListItem