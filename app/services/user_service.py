# 📁 app/services/user_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.db.models.user import User, Role
from app.utils.pagination import PaginationParams, PaginationMeta
from app.core.logger import logger


# ── Allowed sort fields ────────────────────────────────────────────────────────
SORT_FIELDS = {
    "name_asc":       User.name.asc(),
    "name_desc":      User.name.desc(),
    "email_asc":      User.email.asc(),
    "email_desc":     User.email.desc(),
    "created_at_asc": User.created_at.asc(),
    "created_at_desc":User.created_at.desc(),
}


# ── Get all users (admin only) ─────────────────────────────────────────────────
async def get_users(
    db: AsyncSession,
    params: PaginationParams,
    is_active: bool = None,
    is_verified: bool = None,
    role: str = None,
) -> tuple[list[User], PaginationMeta]:
    logger.info(
        f"Get users | page={params.page} limit={params.limit} "
        f"search={params.search} sort={params.sort} "
        f"is_active={is_active} role={role}"
    )

    # ── Base query ─────────────────────────────────────────────────────────────
    query = (
        select(User)
        .options(selectinload(User.roles))   # eagerly load roles
        .where(User.is_deleted == False)
    )

    # ── Search (name or email) ─────────────────────────────────────────────────
    if params.search:
        keyword = f"%{params.search}%"
        query = query.where(
            or_(
                User.name.ilike(keyword),
                User.email.ilike(keyword),
            )
        )

    # ── Filters ────────────────────────────────────────────────────────────────
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)

    if role:
        query = query.join(User.roles).where(Role.name == role)

    # ── Count total (before pagination) ───────────────────────────────────────
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # ── Sort ───────────────────────────────────────────────────────────────────
    order = SORT_FIELDS.get(params.sort, User.created_at.desc())
    query = query.order_by(order)

    # ── Pagination ─────────────────────────────────────────────────────────────
    query = query.offset(params.offset).limit(params.limit)

    result = await db.execute(query)
    users = result.scalars().all()

    total_pages = (total + params.limit - 1) // params.limit

    meta = PaginationMeta(
        total=total,
        page=params.page,
        limit=params.limit,
        total_pages=total_pages,
    )

    return list(users), meta


# ── Assign role to user ────────────────────────────────────────────────────────
async def assign_role_to_user(
    db: AsyncSession,
    user_id: str,
    role_name: str,
) -> User:
    from sqlalchemy.orm import selectinload
    from app.db.models.user import Role

    logger.info(f"Assign role | user_id={user_id} role={role_name}")

    # Get user
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get role
    result = await db.execute(
        select(Role).where(Role.name == role_name, Role.is_deleted == False)
    )
    role = result.scalar_one_or_none()

    if not role:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found",
        )

    # Assign if not already assigned
    existing_role_names = {r.name for r in user.roles}
    if role_name in existing_role_names:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has role '{role_name}'",
        )

    user.roles.append(role)
    await db.flush()
    await db.refresh(user)

    logger.info(f"Role assigned | user_id={user_id} role={role_name}")
    return user