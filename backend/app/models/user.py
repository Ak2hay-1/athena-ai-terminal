"""
User Model.

Stores Athena user accounts.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class UserRole(str, Enum):
    """
    User roles.
    """

    ADMIN = "ADMIN"

    TRADER = "TRADER"

    VIEWER = "VIEWER"


class User(BaseModel):
    """
    Athena User.
    """

    __tablename__ = "users"

    __table_args__ = (

        Index(
            "idx_users_email",
            "email",
        ),

        Index(
            "idx_users_username",
            "username",
        ),

    )

    # ======================================================
    # Identity
    # ======================================================

    username: Mapped[str] = mapped_column(

        String(50),

        unique=True,

        nullable=False,

    )

    email: Mapped[str] = mapped_column(

        String(255),

        unique=True,

        nullable=False,

    )

    full_name: Mapped[str] = mapped_column(

        String(255),

        nullable=False,

    )

    # ======================================================
    # Authentication
    # ======================================================

    password_hash: Mapped[str] = mapped_column(

        String(255),

        nullable=False,

    )

    # ======================================================
    # Authorization
    # ======================================================

    role: Mapped[UserRole] = mapped_column(

        SQLEnum(
            UserRole,
            name="user_role",
        ),

        default=UserRole.TRADER,

        nullable=False,

    )

    # ======================================================
    # Status
    # ======================================================

    is_active: Mapped[bool] = mapped_column(

        Boolean,

        default=True,

        nullable=False,

    )

    is_verified: Mapped[bool] = mapped_column(

        Boolean,

        default=False,

        nullable=False,

    )

    is_superuser: Mapped[bool] = mapped_column(

        Boolean,

        default=False,

        nullable=False,

    )

    # ======================================================
    # Login Tracking
    # ======================================================

    last_login: Mapped[datetime | None] = mapped_column(

        DateTime(timezone=True),

        nullable=True,

    )

    password_changed_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        server_default=func.now(),

        nullable=False,

    )

    # ======================================================
    # Helpers
    # ======================================================

    @property
    def display_name(self) -> str:
        """
        Preferred display name.
        """

        return self.full_name or self.username

    def __repr__(self) -> str:

        return (

            f"<User("

            f"id={self.id}, "

            f"username='{self.username}', "

            f"role='{self.role.value}'"

            f")>"

        )