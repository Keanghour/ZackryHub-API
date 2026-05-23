# 📁 app/routes/users.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import require_roles, get_current_user
from app.schemas.user import UserListItem, UserRoleData
from app.schemas.auth import MeResponse, MeData
from app.schemas.role import (
    AssignRoleRequest, AssignRoleResponse,
    RemoveRoleRequest, RemoveRoleResponse,
    UserRolesResponse, RoleItem, PermissionItem,
)
from app.services.user_service import get_users
from app.services.role_service import (
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
)
from app.utils.pagination import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ── GET /api/v1/users ──────────────────────────────────────────────────────────
@router.get("", response_model=PaginatedResponse[UserListItem], summary="Get all users (Admin only)")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, description="Search by name or email"),
    sort: str = Query("created_at_desc", description="name_asc | name_desc | email_asc | email_desc | created_at_asc | created_at_desc"),
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    role: Optional[str] = Query(None),
):
    params = PaginationParams(page=page, limit=limit, search=search, sort=sort)
    users, meta = await get_users(db, params, is_active=is_active, is_verified=is_verified, role=role)
    data = [
        UserListItem(
            id=u.id, name=u.name, email=u.email,
            is_active=u.is_active, is_verified=u.is_verified,
            roles=[UserRoleData(id=r.id, name=r.name) for r in u.roles],
            created_at=u.created_at,
        )
        for u in users
    ]
    return PaginatedResponse[UserListItem](success=True, data=data, meta=meta)


# ── GET /api/v1/users/me ───────────────────────────────────────────────────────
@router.get("/me", response_model=MeResponse, summary="Get my own profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return MeResponse(
        success=True,
        data=MeData(
            id=current_user.id, name=current_user.name,
            email=current_user.email, is_active=current_user.is_active,
            is_verified=current_user.is_verified,
        ),
    )


# ── GET /api/v1/users/{user_id}/roles ─────────────────────────────────────────
@router.get("/{user_id}/roles", response_model=UserRolesResponse, summary="Get roles of a user (Admin only)")
async def get_roles_of_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    roles = await get_user_roles(db, str(user_id))
    return UserRolesResponse(
        success=True,
        data=[
            RoleItem(
                id=r.id, name=r.name, description=r.description,
                permissions=[
                    PermissionItem(id=p.id, name=p.name, description=p.description)
                    for p in r.permissions
                ],
            )
            for r in roles
        ],
    )


# ── POST /api/v1/users/{user_id}/assign-role ──────────────────────────────────
@router.post("/{user_id}/assign-role", response_model=AssignRoleResponse, summary="Assign role to user (Admin only)")
async def assign_role(
    user_id: UUID,
    payload: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    roles = await assign_role_to_user(db, str(user_id), payload.role_name)
    return AssignRoleResponse(
        success=True,
        message=f"Role '{payload.role_name}' assigned successfully",
        data=[{"id": str(r.id), "name": r.name} for r in roles],
    )


# ── DELETE /api/v1/users/{user_id}/remove-role ────────────────────────────────
@router.delete("/{user_id}/remove-role", response_model=RemoveRoleResponse, summary="Remove role from user (Admin only)")
async def remove_role(
    user_id: UUID,
    payload: RemoveRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    await remove_role_from_user(db, str(user_id), payload.role_name)
    return RemoveRoleResponse(
        success=True,
        message=f"Role '{payload.role_name}' removed successfully",
    )