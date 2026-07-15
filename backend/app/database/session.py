"""
Database Session Management.

Provides SQLAlchemy sessions for:
- FastAPI
- Background Jobs
- Scheduler
- Services
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.database.database import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency.

    Example:

        db: Session = Depends(get_db)
    """

    db = SessionLocal()

    try:
        yield db

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()