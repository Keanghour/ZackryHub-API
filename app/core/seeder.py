# 📁 app/core/seeder.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from sqlalchemy.orm import selectinload

from app.db.models.user import Role, Permission, User, role_permissions, user_roles
from app.core.logger import logger
from app.core.security import hash_password


ROLES_PERMISSIONS = {
    "super_admin": [
        "create_product", "update_product", "delete_product",
        "view_orders", "manage_orders",
        "manage_inventory",
        "view_reports",
        "manage_users",
        "manage_roles",
    ],
    "admin": [
        "create_product", "update_product", "delete_product",
        "view_orders", "manage_orders",
        "manage_inventory",
        "view_reports",
        "manage_users",
    ],
    "manager": [
        "view_orders", "manage_orders",
        "manage_inventory",
        "view_reports",
    ],
    "staff": [
        "view_orders",
        "manage_inventory",
    ],
    "customer": [
        "view_orders",
    ],
}

# ── Super user default credentials ────────────────────────────────────────────
SUPER_USER_EMAIL    = "root@gmail.com"
SUPER_USER_PASSWORD = "root123456"
SUPER_USER_NAME     = "Super Admin"


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    logger.info("🌱 Seeder     : checking roles & permissions...")

    all_perm_names = set(
        p for perms in ROLES_PERMISSIONS.values() for p in perms
    )

    # ── Step 1: Load existing permissions ──────────────────────────────────────
    result = await db.execute(select(Permission))
    perm_map: dict[str, Permission] = {p.name: p for p in result.scalars().all()}

    # ── Step 2: Create missing permissions ────────────────────────────────────
    for name in all_perm_names:
        if name not in perm_map:
            perm = Permission(name=name)
            db.add(perm)
            await db.flush()
            perm_map[name] = perm
            logger.info(f"   ✅ Permission created : {name}")

    # ── Step 3: Load existing roles ────────────────────────────────────────────
    result = await db.execute(select(Role))
    role_map: dict[str, Role] = {r.name: r for r in result.scalars().all()}

    # ── Step 4: Create missing roles ──────────────────────────────────────────
    for name in ROLES_PERMISSIONS:
        if name not in role_map:
            role = Role(name=name)
            db.add(role)
            await db.flush()
            role_map[name] = role
            logger.info(f"   ✅ Role created       : {name}")

    # ── Step 5: Load existing role_permissions links ───────────────────────────
    result = await db.execute(select(role_permissions))
    existing_links: set[tuple] = {
        (row.role_id, row.permission_id)
        for row in result.fetchall()
    }

    # ── Step 6: Insert missing role-permission links ───────────────────────────
    for role_name, perm_names in ROLES_PERMISSIONS.items():
        role = role_map[role_name]
        for perm_name in perm_names:
            perm = perm_map[perm_name]
            if (role.id, perm.id) not in existing_links:
                await db.execute(
                    insert(role_permissions).values(
                        role_id=role.id,
                        permission_id=perm.id,
                    )
                )
                existing_links.add((role.id, perm.id))

    logger.info("🌱 Seeder     : ✅ roles & permissions ready")

    # ── Step 7: Seed super user ────────────────────────────────────────────────
    await seed_super_user(db, role_map)

    await db.commit()


async def seed_super_user(db: AsyncSession, role_map: dict[str, Role]) -> None:
    logger.info("👑 Seeder     : checking super user...")

    # Check if super user already exists
    result = await db.execute(
        select(User).where(User.email == SUPER_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create super user
        user = User(
            name=SUPER_USER_NAME,
            email=SUPER_USER_EMAIL,
            password_hash=hash_password(SUPER_USER_PASSWORD),
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.flush()
        logger.info(f"   ✅ Super user created  : {SUPER_USER_EMAIL}")
    else:
        logger.info(f"   ✅ Super user exists   : {SUPER_USER_EMAIL}")

    # Check if super_admin role already assigned
    result = await db.execute(
        select(user_roles).where(
            user_roles.c.user_id == user.id,
            user_roles.c.role_id == role_map["super_admin"].id,
        )
    )
    if not result.fetchone():
        await db.execute(
            insert(user_roles).values(
                user_id=user.id,
                role_id=role_map["super_admin"].id,
            )
        )
        logger.info(f"   ✅ Role assigned       : super_admin → {SUPER_USER_EMAIL}")

    logger.info("👑 Seeder     : ✅ super user ready")