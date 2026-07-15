"""
Base Service.

Provides common database operations for all services.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logger import logger


class BaseService:
    """
    Base class for all services.

    Responsibilities
    ----------------
    - Database transaction management
    - Refresh entities
    - Rollback on errors
    - Logging helper
    """

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    # ======================================================
    # Transaction
    # ======================================================

    def commit(self) -> None:
        """
        Commit current transaction.
        """

        try:

            self.db.commit()

        except Exception:

            self.db.rollback()

            raise

    def rollback(self) -> None:
        """
        Roll back current transaction.
        """

        self.db.rollback()

    # ======================================================
    # Entity
    # ======================================================

    def refresh(
        self,
        instance,
    ) -> None:
        """
        Refresh ORM instance.
        """

        self.db.refresh(instance)

    def add(
        self,
        instance,
    ) -> None:
        """
        Add entity to session.
        """

        self.db.add(instance)

    def delete(
        self,
        instance,
    ) -> None:
        """
        Delete entity.
        """

        self.db.delete(instance)

    # ======================================================
    # Logging
    # ======================================================

    @property
    def logger(self):
        """
        Service logger.
        """

        return logger