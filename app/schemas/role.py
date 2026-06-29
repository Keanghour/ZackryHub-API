# 📁 app/schemas/role.py

from pydantic import BaseModel
from uuid import UUID
from typing import List
from app.schemas.base import BaseResponse


class PermissionItem(BaseModel):
    id:          UUID
    name:        str
    description: str | None = None
    class Config:
        from_attributes = True


class RoleItem(BaseModel):
    id:          UUID
    name:        str
    description: str | None = None
    permissions: List[PermissionItem] = []
    class Config:
        from_attributes = True


class RoleListResponse(BaseResponse):
    code:    int  = 200
    data: List[RoleItem]


class RoleDetailResponse(BaseResponse):
    code:    int  = 200
    data: RoleItem


class AssignRoleRequest(BaseModel):
    role_name: str


class AssignRoleResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Role assigned successfully"
    data:    List[dict] = []


class RemoveRoleRequest(BaseModel):
    role_name: str


class RemoveRoleResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Role removed successfully"


class UserRolesResponse(BaseResponse):
    code:    int  = 200
    data: List[RoleItem]