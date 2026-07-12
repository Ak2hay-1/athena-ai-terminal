"""
Athena Terminal - Application Entry Point.
"""

from fastapi import FastAPI

from app.api.router import router
from app.core.lifespan import lifespan
from app.core.settings import settings
from app.database.base import Base
from app.database.database import engine

# Import models so SQLAlchemy registers them
from app.models import MarketCandle  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/version", tags=["System"])
def version():
    """
    Returns application version information.
    """
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }