from fastapi import FastAPI

from app.api.router import router
from app.core.lifespan import lifespan
from app.core.settings import settings
from app.database.base import Base
from app.database.database import engine

from app.models import MarketCandle

from app.websocket.routes import router as websocket_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(websocket_router)


@app.get("/version", tags=["System"])
def version():

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }