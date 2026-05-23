# 📁 app/routes/auth.py

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.core.config import settings
from app.schemas.auth import (
    RegisterRequest, RegisterResponse, RegisterData,
    LoginRequest, LoginResponse, LoginData,
    RefreshTokenRequest, RefreshTokenResponse, RefreshTokenData,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    MeResponse, MeData,
    UpdateMeRequest, UpdateMeResponse,
    ChangePasswordRequest, ChangePasswordResponse,
    LogoutRequest, LogoutResponse,
)
from app.services.auth_service import (
    register_user, login_user, refresh_access_token,
    forgot_password, reset_password,
    get_me, update_me, change_password, logout,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── POST /api/v1/auth/register ─────────────────────────────────────────────────
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload)
    return RegisterResponse(
        success=True,
        message="User registered successfully",
        data=RegisterData(id=user.id, name=user.name, email=user.email),
    )


# ── POST /api/v1/auth/login ────────────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    tokens = await login_user(db, payload)
    return LoginResponse(
        success=True,
        message="Login successful",
        data=LoginData(**tokens),
    )


# ── POST /api/v1/auth/refresh ──────────────────────────────────────────────────
@router.post("/refresh", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh(request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    result = await refresh_access_token(db, payload.refresh_token)
    return RefreshTokenResponse(
        success=True,
        data=RefreshTokenData(access_token=result["access_token"]),
    )


# ── POST /api/v1/auth/forgot-password ─────────────────────────────────────────
@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def forgot_password_route(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await forgot_password(db, payload.email)
    return ForgotPasswordResponse(success=True, message="Reset link sent to email")


# ── POST /api/v1/auth/reset-password ──────────────────────────────────────────
@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def reset_password_route(request: Request, payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await reset_password(db, payload.token, payload.new_password)
    return ResetPasswordResponse(success=True, message="Password reset successfully")


# ── GET /api/v1/auth/me ────────────────────────────────────────────────────────
@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me(current_user: User = Depends(get_current_user)):
    user = await get_me(current_user)
    return MeResponse(
        success=True,
        data=MeData(
            id=user.id, name=user.name, email=user.email,
            is_active=user.is_active, is_verified=user.is_verified,
        ),
    )


# ── PUT /api/v1/auth/me ────────────────────────────────────────────────────────
@router.put("/me", response_model=UpdateMeResponse, status_code=status.HTTP_200_OK)
async def update_me_route(
    payload: UpdateMeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await update_me(db, current_user, payload)
    return UpdateMeResponse(
        success=True,
        message="Profile updated successfully",
        data=MeData(
            id=user.id, name=user.name, email=user.email,
            is_active=user.is_active, is_verified=user.is_verified,
        ),
    )


# ── PUT /api/v1/auth/change-password ──────────────────────────────────────────
@router.put("/change-password", response_model=ChangePasswordResponse, status_code=status.HTTP_200_OK)
async def change_password_route(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await change_password(db, current_user, payload)
    return ChangePasswordResponse(success=True, message="Password changed successfully")


# ── POST /api/v1/auth/logout ───────────────────────────────────────────────────
@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout_route(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await logout(db, current_user, payload.refresh_token)
    return LogoutResponse(success=True, message="Logged out successfully")