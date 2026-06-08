# 📁 app/services/auth_service.py

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.db.models.user import User, RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.config import settings
from app.core.logger import auth_logger


# ── Register ───────────────────────────────────────────────────────────────────

async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    auth_logger.info(f"Register attempt | email={payload.email}")

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == payload.email, User.is_deleted == False)
    )
    existing = result.scalar_one_or_none()

    if existing:
        auth_logger.warning(f"Register failed | email={payload.email} | reason=already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    auth_logger.info(f"Register success | user_id={new_user.id} | email={new_user.email}")
    return new_user


# ── Login ──────────────────────────────────────────────────────────────────────

async def login_user(db: AsyncSession, payload: LoginRequest) -> dict:
    auth_logger.info(f"Login attempt | email={payload.email}")

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == payload.email, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    # Validate user and password
    if not user or not verify_password(payload.password, user.password_hash):
        auth_logger.warning(f"Login failed | email={payload.email} | reason=invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        auth_logger.warning(f"Login failed | email={payload.email} | reason=account deactivated")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Generate tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Save refresh token to DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.flush()

    auth_logger.info(f"Login success | user_id={user.id} | email={user.email}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ── Refresh Token ──────────────────────────────────────────────────────────────

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
    from datetime import datetime, timezone
    from app.core.security import decode_token

    auth_logger.info("Refresh token attempt")

    # Decode the refresh token
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        auth_logger.warning("Refresh failed | reason=invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check token exists in DB and is not revoked
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.is_deleted == False,
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        auth_logger.warning("Refresh failed | reason=token not found or revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or revoked"
        )

    # Check token expiry
    if db_token.expires_at < datetime.now(timezone.utc):
        auth_logger.warning(f"Refresh failed | reason=token expired | user_id={db_token.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    # Get user
    result = await db.execute(
        select(User).where(
            User.id == db_token.user_id,
            User.is_deleted == False,
            User.is_active == True,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        auth_logger.warning(f"Refresh failed | reason=user not found | user_id={db_token.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    # Issue new access token
    token_data = {"sub": str(user.id), "email": user.email}
    new_access_token = create_access_token(token_data)

    auth_logger.info(f"Refresh success | user_id={user.id} | email={user.email}")

    return {"access_token": new_access_token}


# ── Forgot Password ────────────────────────────────────────────────────────────

async def forgot_password(db: AsyncSession, email: str) -> None:
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.db.models.user import PasswordResetToken
    from app.core.email import send_reset_password_email

    auth_logger.info(f"Forgot password attempt | email={email}")

    # Find user — always return success even if email not found (security best practice)
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if not user:
        auth_logger.warning(f"Forgot password | email={email} | reason=user not found (silenced)")
        return  # Don't reveal if email exists

    # Invalidate any existing unused tokens for this user
    existing = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.is_deleted == False,
        )
    )
    for old_token in existing.scalars().all():
        old_token.is_used = True

    # Generate secure token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.flush()

    # Send email
    await send_reset_password_email(
        email=user.email,
        name=user.name,
        token=token,
    )

    auth_logger.info(f"Reset token created | user_id={user.id} | email={user.email}")


# ── Reset Password ─────────────────────────────────────────────────────────────

async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    from datetime import datetime, timezone
    from app.db.models.user import PasswordResetToken

    auth_logger.info("Reset password attempt")

    # Find the token
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.is_deleted == False,
        )
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        auth_logger.warning("Reset password failed | reason=invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token"
        )

    # Check expiry
    if reset_token.expires_at < datetime.now(timezone.utc):
        auth_logger.warning("Reset password failed | reason=token expired")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Get user
    result = await db.execute(
        select(User).where(
            User.id == reset_token.user_id,
            User.is_deleted == False,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password and mark token as used
    user.password_hash = hash_password(new_password)
    reset_token.is_used = True
    await db.flush()

    auth_logger.info(f"Password reset success | user_id={user.id} | email={user.email}")


# ── Get Me ─────────────────────────────────────────────────────────────────────

async def get_me(user: User) -> User:
    """Simply return the current user — already loaded by dependency."""
    auth_logger.info(f"Get me | user_id={user.id}")
    return user


# ── Update Me ──────────────────────────────────────────────────────────────────

async def update_me(db: AsyncSession, user: User, payload) -> User:
    auth_logger.info(f"Update me attempt | user_id={user.id}")

    # Check new email not taken by another user
    if payload.email and payload.email != user.email:
        result = await db.execute(
            select(User).where(
                User.email == payload.email,
                User.is_deleted == False,
                User.id != user.id,
            )
        )
        if result.scalar_one_or_none():
            auth_logger.warning(f"Update me failed | reason=email taken | email={payload.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use",
            )
        user.email = payload.email

    if payload.name:
        user.name = payload.name

    await db.flush()
    await db.refresh(user)

    auth_logger.info(f"Update me success | user_id={user.id}")
    return user


# ── Change Password ────────────────────────────────────────────────────────────

async def change_password(db: AsyncSession, user: User, payload) -> None:
    auth_logger.info(f"Change password attempt | user_id={user.id}")

    # Verify current password
    if not verify_password(payload.current_password, user.password_hash):
        auth_logger.warning(f"Change password failed | user_id={user.id} | reason=wrong current password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Prevent same password
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.password_hash = hash_password(payload.new_password)
    await db.flush()

    auth_logger.info(f"Change password success | user_id={user.id}")


# ── Logout ─────────────────────────────────────────────────────────────────────

async def logout(db: AsyncSession, user: User, refresh_token: str) -> None:
    auth_logger.info(f"Logout attempt | user_id={user.id}")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False,
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token",
        )

    db_token.is_revoked = True
    await db.flush()

    auth_logger.info(f"Logout success | user_id={user.id}")