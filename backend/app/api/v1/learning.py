"""
Learning API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.auth.dependencies import require_viewer
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import get_db
from app.models.user import User
from app.services.learning_service import LearningService

router = APIRouter(
    prefix="/learning",
    tags=["Learning"],
)


def get_learning_service(
    db: Session = Depends(get_db),
) -> LearningService:
    return LearningService(db)


@router.get(
    "/stats",
    summary="Learning statistics for symbol/timeframe",
)
def learning_stats(
    symbol: str = Query(default="XAUUSD"),
    timeframe: str = Query(default="M1"),
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)
    return service.get_stats(symbol, timeframe)


@router.get(
    "/weights",
    summary="Current adaptive confluence weights",
)
def learning_weights(
    symbol: str = Query(default="XAUUSD"),
    timeframe: str = Query(default="M1"),
    _: User = Depends(require_admin),
    service: LearningService = Depends(get_learning_service),
):
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)
    return service.weights.get_weights(symbol, timeframe)


@router.post(
    "/retrain",
    summary="Trigger model retraining",
)
def retrain(
    _: User = Depends(require_admin),
    service: LearningService = Depends(get_learning_service),
):
    return service.retrain_all()


@router.post(
    "/label",
    summary="Label pending recommendation outcomes",
)
def label_outcomes(
    _: User = Depends(require_admin),
    service: LearningService = Depends(get_learning_service),
):
    return {"labeled": service.run_labeling()}
