"""
Authentication Dependencies.
"""

from __future__ import annotations

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.security import security
from app.database.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# ==========================================================
# OAuth2
# ==========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


# ==========================================================
# Service Dependency
# ==========================================================

def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    """
    Authentication service dependency.
    """
    return AuthService(db)


# ==========================================================
# Current User
# ==========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Return the authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        if security.get_token_type(token) != "access":
            raise credentials_exception

        user_id = int(
            security.get_subject(token)
        )

    except JWTError:
        raise credentials_exception

    user = service.get_user(user_id)

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    return user


# ==========================================================
# Active User
# ==========================================================

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Active authenticated user.
    """

    return current_user


# ==========================================================
# Administrator
# ==========================================================

def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Administrator only.
    """

    if current_user.role != UserRole.ADMIN:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user


# ==========================================================
# Trader
# ==========================================================

def require_trader(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Trader or Administrator.
    """

    if current_user.role not in (

        UserRole.ADMIN,

        UserRole.TRADER,

    ):

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail="Trader access required.",

        )

    return current_user


# ==========================================================
# Viewer
# ==========================================================

def require_viewer(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Any authenticated user.
    """

    return current_user


# ==========================================================
# Superuser
# ==========================================================

def require_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Superuser only.
    """

    if not current_user.is_superuser:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required.",
        )

    return current_user