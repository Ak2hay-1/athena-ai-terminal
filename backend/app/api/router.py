from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.market import router as market_router
from app.api.system import router as system_router

router = APIRouter()

router.include_router(system_router)
router.include_router(health_router)
router.include_router(market_router)