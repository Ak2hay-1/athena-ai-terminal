"""
Recommendation API.
"""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.recommendation import (
    RecommendationRead,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "/latest",
    response_model=RecommendationRead | None,
)
def latest(
    symbol: str,
    timeframe: str,
    db: Session = Depends(get_db),
):
    """
    Latest recommendation.
    """

    repo = RecommendationRepository(db)

    return repo.get_latest(
        symbol,
        timeframe,
    )


@router.get(
    "/history",
    response_model=list[RecommendationRead],
)
def history(
    symbol: str,
    timeframe: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Recommendation history.
    """

    repo = RecommendationRepository(db)

    return repo.get_history(
        symbol,
        timeframe,
        limit,
    )
