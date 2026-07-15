"""
Database Configuration.

Provides:

- SQLAlchemy Engine
- Session Factory
- Session Dependency
- Database Health Check
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.core.logger import logger
from app.core.settings import settings

# ==========================================================
# Engine
# ==========================================================

engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)

# ==========================================================
# Session Factory
# ==========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

# ==========================================================
# Dependency
# ==========================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI database dependency.

    Creates one SQLAlchemy session per request.

    Commits are handled by the service layer.
    """

    db = SessionLocal()

    try:

        yield db

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

# ==========================================================
# Health Check
# ==========================================================

def check_database_connection() -> bool:
    """
    Check database connectivity.

    Returns
    -------
    bool
        True if database is reachable.
    """

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception as exc:

        logger.exception(
            "Database health check failed: %s",
            exc,
        )

        return False

# ==========================================================
# Utility
# ==========================================================

def get_session() -> Session:
    """
    Create a standalone SQLAlchemy session.

    Intended for scripts, CLI commands,
    background jobs and schedulers.
    """

    return SessionLocal()