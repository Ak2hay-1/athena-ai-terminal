"""
Authentication Service.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.security import security
from app.core.exceptions import ValidationException
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    AdminUserUpdate,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.base_service import BaseService


class AuthService(BaseService):
    """
    Authentication business logic.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:

        super().__init__(db)

        self.users = UserRepository(db)

    # ======================================================
    # Registration
    # ======================================================

    def register(
        self,
        payload: UserCreate,
    ) -> UserRead:

        if self.users.username_exists(payload.username):
            raise ValidationException(
                "Username already exists."
            )

        if self.users.email_exists(payload.email):
            raise ValidationException(
                "Email already exists."
            )

        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=security.hash_password(
                payload.password,
            ),
        )

        self.users.create(user)

        self.commit()

        self.refresh(user)

        self.logger.info(
            "User registered: %s",
            user.username,
        )

        return UserRead.model_validate(user)

    # ======================================================
    # Login
    # ======================================================

    def login(
        self,
        payload: LoginRequest,
    ) -> Token:

        user = self.users.get_by_username(
            payload.username,
        )

        if user is None:
            raise ValidationException(
                "Invalid username or password."
            )

        if not user.is_active:
            raise ValidationException(
                "User account is disabled."
            )

        if not security.verify_password(
            payload.password,
            user.password_hash,
        ):
            raise ValidationException(
                "Invalid username or password."
            )

        user.last_login = datetime.now(
            timezone.utc,
        )

        self.commit()

        self.logger.info(
            "User logged in: %s",
            user.username,
        )

        return Token(
            access_token=security.create_access_token(
                str(user.id),
            ),
            refresh_token=security.create_refresh_token(
                str(user.id),
            ),
        )

    # ======================================================
    # Refresh Token
    # ======================================================

    def refresh_token(
        self,
        payload: RefreshTokenRequest,
    ) -> Token:

        if (
            security.get_token_type(
                payload.refresh_token,
            )
            != "refresh"
        ):
            raise ValidationException(
                "Invalid refresh token."
            )

        user_id = int(
            security.get_subject(
                payload.refresh_token,
            )
        )

        user = self.get_user(user_id)

        if not user.is_active:
            raise ValidationException(
                "User account is disabled."
            )

        return Token(
            access_token=security.create_access_token(
                str(user.id),
            ),
            refresh_token=security.create_refresh_token(
                str(user.id),
            ),
        )

    # ======================================================
    # User
    # ======================================================

    def get_user(
        self,
        user_id: int,
    ) -> User:

        user = self.users.get_by_id(user_id)

        if user is None:
            raise ValidationException(
                "User not found."
            )

        return user

    def get_user_by_id(
        self,
        user_id: int,
    ) -> UserRead:

        return UserRead.model_validate(
            self.get_user(user_id),
        )

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserRead]:

        users = self.users.list(
            skip=skip,
            limit=limit,
        )

        return [
            UserRead.model_validate(user)
            for user in users
        ]

    # ======================================================
    # Update
    # ======================================================

    def update_user(
        self,
        user_id: int,
        payload: UserUpdate,
    ) -> UserRead:

        user = self.get_user(user_id)

        if (
            payload.email
            and payload.email != user.email
            and self.users.email_exists(payload.email)
        ):
            raise ValidationException(
                "Email already exists."
            )

        values = payload.model_dump(exclude_unset=True)

        if "password" in values and values["password"]:
            user.password_hash = security.hash_password(
                values.pop("password"),
            )
            user.password_changed_at = datetime.now(
                timezone.utc,
            )
        else:
            values.pop("password", None)

        self.users.update(user, values)

        self.commit()

        self.refresh(user)

        self.logger.info(
            "User updated: %s",
            user.username,
        )

        return UserRead.model_validate(user)

    def admin_update_user(
        self,
        user_id: int,
        payload: AdminUserUpdate,
        *,
        actor_id: int,
    ) -> UserRead:

        user = self.get_user(user_id)
        values = payload.model_dump(exclude_unset=True)

        if (
            "email" in values
            and values["email"] != user.email
            and self.users.email_exists(values["email"])
        ):
            raise ValidationException(
                "Email already exists."
            )

        if (
            user_id == actor_id
            and "role" in values
            and values["role"] != UserRole.ADMIN
        ):
            raise ValidationException(
                "You cannot demote your own admin role."
            )

        if (
            user_id == actor_id
            and values.get("is_active") is False
        ):
            raise ValidationException(
                "You cannot deactivate your own account."
            )

        self.users.update(user, values)

        self.commit()

        self.refresh(user)

        self.logger.info(
            "Admin updated user: %s",
            user.username,
        )

        return UserRead.model_validate(user)

    def set_role(
        self,
        user_id: int,
        role: UserRole,
        *,
        actor_id: int,
    ) -> UserRead:

        return self.admin_update_user(
            user_id,
            AdminUserUpdate(role=role),
            actor_id=actor_id,
        )

    # ======================================================
    # Password
    # ======================================================

    def change_password(
        self,
        user_id: int,
        payload: ChangePasswordRequest,
    ) -> None:

        user = self.get_user(user_id)

        if not security.verify_password(
            payload.current_password,
            user.password_hash,
        ):
            raise ValidationException(
                "Current password is incorrect."
            )

        user.password_hash = security.hash_password(
            payload.new_password,
        )

        user.password_changed_at = datetime.now(
            timezone.utc,
        )

        self.commit()

        self.logger.info(
            "Password changed: %s",
            user.username,
        )

    # ======================================================
    # Status
    # ======================================================

    def set_active(
        self,
        user_id: int,
        active: bool,
        *,
        actor_id: int | None = None,
    ) -> UserRead:

        if actor_id is not None and user_id == actor_id and not active:
            raise ValidationException(
                "You cannot deactivate your own account."
            )

        user = self.get_user(user_id)

        user.is_active = active

        self.commit()

        self.refresh(user)

        action = "activated" if active else "deactivated"

        self.logger.info(
            "User %s: %s",
            action,
            user.username,
        )

        return UserRead.model_validate(user)

    # ======================================================
    # Delete
    # ======================================================

    def delete(
        self,
        user_id: int,
    ) -> None:

        user = self.get_user(user_id)

        username = user.username

        self.users.delete(user)

        self.commit()

        self.logger.info(
            "User deleted: %s",
            username,
        )