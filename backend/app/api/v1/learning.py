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
from app.models.learning import LearningVersion
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
    "/dashboard",
    summary="Continuous learning dashboard aggregate",
)
def learning_dashboard(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {"success": True, "data": service.get_dashboard()}


@router.get(
    "/features",
    summary="Feature performance analytics",
)
def learning_features(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.features.list_all()],
    }


@router.get(
    "/symbols",
    summary="Symbol performance analytics",
)
def learning_symbols(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.symbols.list_all()],
    }


@router.get(
    "/timeframes",
    summary="Timeframe performance analytics",
)
def learning_timeframes(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.timeframes.list_all()],
    }


@router.get(
    "/regimes",
    summary="Market regime analytics",
)
def learning_regimes(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.regimes.list_all()],
    }


@router.get(
    "/strategies",
    summary="Strategy combination analytics",
)
def learning_strategies(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.strategies.list_all()],
    }


@router.get(
    "/calibration",
    summary="Confidence calibration buckets",
)
def learning_calibration(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    return {
        "success": True,
        "data": [row.to_dict() for row in service.calibration.list_all()],
    }


@router.get(
    "/weights",
    summary="Active confidence weights and recent history",
)
def learning_weights(
    symbol: str = Query(default="XAUUSD"),
    timeframe: str = Query(default="M1"),
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)
    history = service.confidence_weights.list_history(limit=25)
    return {
        "success": True,
        "data": {
            "active": service.confidence_weights.get_active_weights(),
            "version": service.confidence_weights.get_active_version(),
            "confluence_weights": service.weights.get_weights(symbol, timeframe),
            "history": [row.to_dict() for row in history],
        },
    }


@router.get(
    "/history",
    summary="Learning and weight version timeline",
)
def learning_history(
    _: User = Depends(require_viewer),
    service: LearningService = Depends(get_learning_service),
):
    versions = (
        service.db.query(LearningVersion)
        .order_by(LearningVersion.created_at.desc())
        .limit(50)
        .all()
    )
    weights = service.confidence_weights.list_history(limit=50)
    return {
        "success": True,
        "data": {
            "learning_versions": [row.to_dict() for row in versions],
            "weight_history": [row.to_dict() for row in weights],
        },
    }


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


@router.post(
    "/refresh-analytics",
    summary="Recalculate learning analytics tables",
)
def refresh_analytics(
    _: User = Depends(require_admin),
    service: LearningService = Depends(get_learning_service),
):
    return {"success": True, "data": service.refresh_analytics()}


@router.post(
    "/update-weights",
    summary="Run adaptive confidence weight update",
)
def update_weights(
    _: User = Depends(require_admin),
    service: LearningService = Depends(get_learning_service),
):
    result = service.update_confidence_weights(reason="manual")
    return {"success": result is not None, "data": result}
