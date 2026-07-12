"""
Database session management.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()