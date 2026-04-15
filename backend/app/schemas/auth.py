"""Pydantic schemas for authentication endpoints."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.student

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe user representation — never exposes the password hash."""
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    """Fields the user can update on their own profile."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
