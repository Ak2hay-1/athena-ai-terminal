"""
Authentication API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from fastapi import status

from app.auth.dependencies import (
    get_auth_service,
    get_current_active_user,
    require_admin,
)
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==========================================================
# Register
# ==========================================================

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    return service.register(payload)


# ==========================================================
# Login
# ==========================================================

@router.post(
    "/login",
    response_model=Token,
    summary="Login",
)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.login(payload)


# ==========================================================
# Refresh Token
# ==========================================================

@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
def refresh(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh_token(payload)


# ==========================================================
# Current User
# ==========================================================

@router.get(
    "/me",
    response_model=UserRead,
    summary="Current authenticated user",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return UserRead.model_validate(current_user)


# ==========================================================
# Update Profile
# ==========================================================

@router.put(
    "/me",
    response_model=UserRead,
    summary="Update profile",
)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    return service.update_user(
        current_user.id,
        payload,
    )


# ==========================================================
# Change Password
# ==========================================================

@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    service.change_password(
        current_user.id,
        payload,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ==========================================================
# Delete My Account
# ==========================================================

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current account",
)
def delete_me(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    service.delete(
        current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


# ==========================================================
# Admin
# ==========================================================

@router.get(
    "/users",
    response_model=list[UserRead],
    summary="List users",
)
def list_users(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    _: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.list_users(
        skip=skip,
        limit=limit,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Get user",
)
def get_user(
    user_id: int,
    _: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.get_user_by_id(
        user_id,
    )


@router.patch(
    "/users/{user_id}/activate",
    response_model=UserRead,
    summary="Activate user",
)
def activate_user(
    user_id: int,
    _: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.set_active(
        user_id,
        True,
    )


@router.patch(
    "/users/{user_id}/deactivate",
    response_model=UserRead,
    summary="Deactivate user",
)
def deactivate_user(
    user_id: int,
    _: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.set_active(
        user_id,
        False,
    )