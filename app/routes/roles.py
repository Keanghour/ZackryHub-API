# 📁 app/routes/roles.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import require_roles
from app.schemas.role import (
    RoleListResponse, RoleDetailResponse,
    RoleItem, PermissionItem,
)
from app.services.role_service import get_all_roles, get_role_by_id

router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])


# ── GET /api/v1/roles ──────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=RoleListResponse,
    summary="Get all roles with permissions (Admin only)",
)
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    roles = await get_all_roles(db)
    return RoleListResponse(
        success=True,
        data=[
            RoleItem(
                id=r.id,
                name=r.name,
                description=r.description,
                permissions=[
                    PermissionItem(id=p.id, name=p.name, description=p.description)
                    for p in r.permissions
                ],
            )
            for r in roles
        ],
    )


# ── GET /api/v1/roles/{role_id} ────────────────────────────────────────────────
@router.get(
    "/{role_id}",
    response_model=RoleDetailResponse,
    summary="Get role detail with permissions (Admin only)",
)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("super_admin", "admin")),
):
    role = await get_role_by_id(db, str(role_id))
    return RoleDetailResponse(
        success=True,
        data=RoleItem(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                PermissionItem(id=p.id, name=p.name, description=p.description)
                for p in role.permissions
            ],
        ),
    )