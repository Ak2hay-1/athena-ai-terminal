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
    AdminRoleUpdate,
    AdminUserUpdate,
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
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        Path(__file__).resolve().parents[4].joinpath("debug-9c9447.log").open(
            "a", encoding="utf-8"
        ).write(
            json.dumps(
                {
                    "sessionId": "9c9447",
                    "runId": "pre-fix",
                    "hypothesisId": "D",
                    "location": "auth.py:login",
                    "message": "login handler entered",
                    "data": {"username": payload.username[:64]},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    except Exception:
        pass
    # #endregion
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
    current_user: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.set_active(
        user_id,
        True,
        actor_id=current_user.id,
    )


@router.patch(
    "/users/{user_id}/deactivate",
    response_model=UserRead,
    summary="Deactivate user",
)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.set_active(
        user_id,
        False,
        actor_id=current_user.id,
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Update user (admin)",
)
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.admin_update_user(
        user_id,
        payload,
        actor_id=current_user.id,
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=UserRead,
    summary="Update user role",
)
def update_user_role(
    user_id: int,
    payload: AdminRoleUpdate,
    current_user: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    return service.set_role(
        user_id,
        payload.role,
        actor_id=current_user.id,
    )