# 📁 app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from app.schemas.base import BaseResponse


# ── Request Schemas ────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:     str      = Field(..., min_length=2, max_length=100, example="John Doe")
    email:    EmailStr = Field(..., example="john@email.com")
    password: str      = Field(..., min_length=6, max_length=72, example="123456")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr = Field(..., example="root@gmail.com")
    password: str      = Field(..., min_length=1, max_length=72, example="root123456")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


# ── Response Data ──────────────────────────────────────────────────────────────
class RegisterData(BaseModel):
    id:    UUID
    name:  str
    email: str
    class Config:
        from_attributes = True


class RegisterResponse(BaseResponse):
    code:    int  = 201
    message: str  = "User registered successfully"
    data: RegisterData


class LoginData(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class LoginResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Login successful"
    data: LoginData


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="token_here")


class RefreshTokenData(BaseModel):
    access_token: str


class RefreshTokenResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Token refreshed successfully"
    data: RefreshTokenData


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., example="john@email.com")


class ForgotPasswordResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Reset link sent to email"


class ResetPasswordRequest(BaseModel):
    token:        str = Field(..., example="reset_token")
    new_password: str = Field(..., min_length=6, max_length=72, example="newpass123")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class ResetPasswordResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Password reset successfully"


class MeData(BaseModel):
    id:          UUID
    name:        str
    email:       str
    is_active:   bool
    is_verified: bool
    class Config:
        from_attributes = True


class MeResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Success"
    data: MeData


class UpdateMeRequest(BaseModel):
    name:  str       = Field(None, min_length=2, max_length=100)
    email: EmailStr  = Field(None)


class UpdateMeResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Profile updated successfully"
    data: MeData


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=72, example="oldpass123")
    new_password:     str = Field(..., min_length=6, max_length=72, example="newpass123")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        return v


class ChangePasswordResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Password changed successfully"


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., example="token_here")


class LogoutResponse(BaseResponse):
    code:    int  = 200
    message: str  = "Logged out successfully"