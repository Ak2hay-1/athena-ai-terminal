from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings
from app.core.logger import logger
from app.database.database import engine
from app.database.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(router)

logger.info("Athena AI Terminal Started")