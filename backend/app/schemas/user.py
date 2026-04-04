"""Pydantic schemas for user-related API requests and responses."""

import uuid
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.student


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
