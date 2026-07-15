"""
Base SQLAlchemy model for Athena.

Provides:
- Primary key
- created_at
- updated_at
- to_dict()
- update()
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class BaseModel(Base):
    """
    Base model inherited by all database models.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """
        Convert SQLAlchemy model into dictionary.
        """

        result: dict = {}

        for column in self.__table__.columns:

            value = getattr(self, column.name)

            if isinstance(value, datetime):
                value = value.isoformat()

            elif isinstance(value, Decimal):
                value = float(value)

            result[column.name] = value

        return result

    def update(self, **kwargs) -> None:
        """
        Update model attributes.
        """

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(self, key, value)

    def __repr__(self) -> str:

        return (
            f"<{self.__class__.__name__}"
            f"(id={self.id})>"
        )