"""
SQLAlchemy Declarative Base.

Every database model in Athena inherits from this Base.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """

    pass