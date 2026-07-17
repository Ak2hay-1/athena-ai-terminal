"""
User Repository.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    User repository.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:

        super().__init__(
            db,
            User,
        )

    # ======================================================
    # Username
    # ======================================================

    def get_by_username(
        self,
        username: str,
    ) -> User | None:

        stmt = select(User).where(

            func.lower(User.username)
            == username.lower()

        )

        return self.db.scalar(stmt)

    def username_exists(
        self,
        username: str,
    ) -> bool:

        return (

            self.get_by_username(
                username,
            )

            is not None

        )

    # ======================================================
    # Email
    # ======================================================

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        stmt = select(User).where(

            func.lower(User.email)
            == email.lower()

        )

        return self.db.scalar(stmt)

    def email_exists(
        self,
        email: str,
    ) -> bool:

        return (

            self.get_by_email(
                email,
            )

            is not None

        )

    # ======================================================
    # Counts
    # ======================================================

    def count_all(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(User)
            )
            or 0
        )

    def count_active(self) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.is_active.is_(True))
            )
            or 0
        )

    def count_admins(self) -> int:
        from app.models.user import UserRole

        return int(
            self.db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == UserRole.ADMIN)
            )
            or 0
        )