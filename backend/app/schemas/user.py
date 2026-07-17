"""
User Schemas.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.models.user import UserRole


# ==========================================================
# Authentication
# ==========================================================


class LoginRequest(BaseModel):
    """
    User login request.
    """

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=6,
    )


class Token(BaseModel):
    """
    JWT token response.
    """

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request.
    """

    refresh_token: str


# ==========================================================
# User Base
# ==========================================================


class UserBase(BaseModel):
    """
    Base user schema.
    """

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    full_name: str = Field(
        min_length=1,
        max_length=255,
    )


# ==========================================================
# Create
# ==========================================================


class UserCreate(UserBase):
    """
    User registration.
    """

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# ==========================================================
# Update
# ==========================================================


class UserUpdate(BaseModel):
    """
    User update.
    """

    email: EmailStr | None = None

    full_name: str | None = None

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )


class AdminUserUpdate(BaseModel):
    """
    Admin update for another user.
    """

    email: EmailStr | None = None

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    role: UserRole | None = None

    is_active: bool | None = None

    is_verified: bool | None = None


class AdminRoleUpdate(BaseModel):
    """
    Admin role assignment.
    """

    role: UserRole


# ==========================================================
# Read
# ==========================================================


class UserRead(UserBase):
    """
    User response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    role: UserRole

    is_active: bool

    is_verified: bool

    is_superuser: bool

    last_login: datetime | None = None

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Password
# ==========================================================


class ChangePasswordRequest(BaseModel):
    """
    Password change request.
    """

    current_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )
