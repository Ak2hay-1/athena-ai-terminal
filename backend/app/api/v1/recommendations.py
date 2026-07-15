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


@router.get(
    "/count",
)
def recommendation_count(
    db: Session = Depends(get_db),
):
    """
    Total stored recommendations for the default
    XAUUSD M1 stream.
    """

    repo = RecommendationRepository(db)

    return {
        "count": len(
            repo.get_history(
                symbol="XAUUSD",
                timeframe="M1",
                limit=100000,
            )
        )
    }
