# 📁 app/schemas/user.py

from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime
from app.schemas.base import BaseResponse


class UserRoleData(BaseModel):
    id:   UUID
    name: str
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id:          UUID
    name:        str
    email:       str
    is_active:   bool
    is_verified: bool
    roles:       List[UserRoleData] = []
    created_at:  datetime
    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    role_name: str


class AssignRoleResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Role assigned successfully"
    data:    List[dict] = []