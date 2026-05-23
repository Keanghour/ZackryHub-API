# 📁 app/services/role_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.db.models.user import Role, Permission, User, role_permissions, user_roles
from app.core.logger import logger


# ── Get all roles with permissions ─────────────────────────────────────────────
async def get_all_roles(db: AsyncSession) -> list[Role]:
    logger.info("Get all roles")
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.is_deleted == False)
        .order_by(Role.name)
    )
    return list(result.scalars().all())


# ── Get single role with permissions ───────────────────────────────────────────
async def get_role_by_id(db: AsyncSession, role_id: str) -> Role:
    logger.info(f"Get role | role_id={role_id}")
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id, Role.is_deleted == False)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


# ── Get roles of a specific user ───────────────────────────────────────────────
async def get_user_roles(db: AsyncSession, user_id: str) -> list[Role]:
    logger.info(f"Get user roles | user_id={user_id}")

    # Check user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get roles via join table directly — no lazy load
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .join(user_roles, user_roles.c.role_id == Role.id)
        .where(user_roles.c.user_id == user_id)
        .where(Role.is_deleted == False)
    )
    return list(result.scalars().all())


# ── Assign role to user ────────────────────────────────────────────────────────
async def assign_role_to_user(
    db: AsyncSession,
    user_id: str,
    role_name: str,
) -> list[Role]:
    logger.info(f"Assign role | user_id={user_id} role={role_name}")

    # Check user
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check role
    result = await db.execute(
        select(Role).where(Role.name == role_name, Role.is_deleted == False)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found. Available: super_admin, admin, manager, staff, customer",
        )

    # Check if already assigned via join table
    result = await db.execute(
        select(user_roles).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role.id,
        )
    )
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has role '{role_name}'",
        )

    # Insert directly into join table
    await db.execute(
        insert(user_roles).values(user_id=user_id, role_id=role.id)
    )
    await db.flush()

    logger.info(f"Role assigned | user_id={user_id} role={role_name}")

    # Return updated roles
    return await get_user_roles(db, user_id)


# ── Remove role from user ──────────────────────────────────────────────────────
async def remove_role_from_user(
    db: AsyncSession,
    user_id: str,
    role_name: str,
) -> None:
    logger.info(f"Remove role | user_id={user_id} role={role_name}")

    # Check user
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check role
    result = await db.execute(
        select(Role).where(Role.name == role_name, Role.is_deleted == False)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role '{role_name}' not found")

    # Check if assigned
    result = await db.execute(
        select(user_roles).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role.id,
        )
    )
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role '{role_name}'",
        )

    # Remove from join table
    await db.execute(
        delete(user_roles).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role.id,
        )
    )
    await db.flush()

    logger.info(f"Role removed | user_id={user_id} role={role_name}")