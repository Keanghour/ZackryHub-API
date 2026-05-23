# 📁 app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID


# ── Request Schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="John Doe")
    email: EmailStr = Field(..., example="john@email.com")
    password: str = Field(..., min_length=6, max_length=72, example="123456")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="root@gmail.com")
    password: str = Field(..., min_length=1, max_length=72, example="root123456")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


# ── Response Schemas ───────────────────────────────────────────────────────────

class RegisterData(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "User registered successfully"
    data: RegisterData


class LoginData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    success: bool = True
    message: str = "Login successful"
    data: LoginData


# ── Error Response ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    success: bool = False
    message: str


# ── Refresh Token ──────────────────────────────────────────────────────────────

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="token_here")


class RefreshTokenData(BaseModel):
    access_token: str


class RefreshTokenResponse(BaseModel):
    success: bool = True
    data: RefreshTokenData


# ── Forgot Password ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., example="john@email.com")


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Reset link sent to email"


# ── Reset Password ─────────────────────────────────────────────────────────────

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., example="reset_token")
    new_password: str = Field(..., min_length=6, max_length=72, example="newpass123")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password reset successfully"


# ── Get Me ─────────────────────────────────────────────────────────────────────

class MeData(BaseModel):
    id: UUID
    name: str
    email: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    success: bool = True
    data: MeData


# ── Update Me ──────────────────────────────────────────────────────────────────

class UpdateMeRequest(BaseModel):
    name: str = Field(None, min_length=2, max_length=100, example="John Updated")
    email: EmailStr = Field(None, example="john_new@email.com")


class UpdateMeResponse(BaseModel):
    success: bool = True
    message: str = "Profile updated successfully"
    data: MeData


# ── Change Password ────────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=72, example="oldpass123")
    new_password: str = Field(..., min_length=6, max_length=72, example="newpass123")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class ChangePasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password changed successfully"


# ── Logout ─────────────────────────────────────────────────────────────────────

class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., example="token_here")


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logged out successfully"