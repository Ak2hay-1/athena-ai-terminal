"""
Recommendation API.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_viewer
from app.database.database import get_db
from app.models.user import User
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.probability import SimilarRecommendationItem
from app.schemas.probability import TradeComparisonResult
from app.schemas.recommendation import RecommendationRead
from app.schemas.recommendation import SymbolScenarioRead
from app.schemas.recommendation import TimeframeSignalSnapshot
from app.services.historical_similarity_service import HistoricalSimilarityService
from app.services.trade_comparison_service import TradeComparisonService

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

_TF_ORDER = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def _build_scenario(repo: RecommendationRepository, symbol: str) -> SymbolScenarioRead:
    sym = symbol.upper().strip()
    by_tf = repo.get_latest_per_timeframe(sym)
    snapshots: list[TimeframeSignalSnapshot] = []
    for tf in _TF_ORDER:
        row = by_tf.get(tf)
        if row is None:
            continue
        snapshots.append(
            TimeframeSignalSnapshot(
                timeframe=tf,
                signal=row.signal,
                confidence=int(row.confidence or 0),
                trend=row.trend,
                confluence=int(row.confluence or 0),
                recommendation_id=row.id,
                created_at=row.created_at,
            )
        )
    # Include any unexpected TFs at the end.
    for tf, row in by_tf.items():
        if tf in _TF_ORDER:
            continue
        snapshots.append(
            TimeframeSignalSnapshot(
                timeframe=tf,
                signal=row.signal,
                confidence=int(row.confidence or 0),
                trend=row.trend,
                confluence=int(row.confluence or 0),
                recommendation_id=row.id,
                created_at=row.created_at,
            )
        )
    best = repo.get_best_for_symbol(sym) if by_tf else None
    return SymbolScenarioRead(symbol=sym, best=best, by_timeframe=snapshots)


@router.get(
    "/latest",
    response_model=RecommendationRead | None,
)
def latest(
    symbol: str,
    timeframe: str | None = Query(
        default=None,
        description="Optional. When omitted, returns the best overall setup across timeframes.",
    ),
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """
    Latest recommendation for a symbol.

    Pass ``timeframe`` for a TF-specific row; omit it for Athena's overall
    scenario pick (actionable setups preferred across all TFs).
    """

    repo = RecommendationRepository(db)
    tf = (timeframe or "").strip() or None

    return repo.get_latest(symbol, tf)


@router.get(
    "/scenario",
    response_model=SymbolScenarioRead,
)
def scenario(
    symbol: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """
    Overall trade scenario: best setup plus latest signal per timeframe.
    """

    return _build_scenario(RecommendationRepository(db), symbol)


@router.get(
    "/history",
    response_model=list[RecommendationRead],
)
def history(
    timeframe: str | None = Query(
        default=None,
        description="Optional. When omitted with a symbol, returns history across all TFs.",
    ),
    symbol: str | None = Query(default=None),
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """
    Recommendation history.

    Omit ``timeframe`` to include all timeframes (overall scenario history).
    Omit ``symbol`` to return rows across all pairs (optionally scoped by TF).
    """

    repo = RecommendationRepository(db)
    normalized = (symbol or "").strip().upper() or None
    tf = (timeframe or "").strip() or None

    return repo.get_history(
        normalized,
        tf,
        limit,
    )


@router.get(
    "/count",
)
def recommendation_count(
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
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


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationRead,
)
def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """Fetch a single recommendation by id."""
    repo = RecommendationRepository(db)
    row = repo.read(recommendation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    return row


@router.get(
    "/{recommendation_id}/similar",
    response_model=list[SimilarRecommendationItem],
)
def similar_recommendations(
    recommendation_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """Return the most similar historical recommendations."""
    repo = RecommendationRepository(db)
    row = repo.read(recommendation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )

    service = HistoricalSimilarityService(db)
    rows = service.find_similar(
        row,
        top_n=max(1, min(limit, 50)),
        labeled_only=True,
    )
    # Fall back to unlabeled history if no labeled peers.
    if not rows:
        rows = service.find_similar(
            row,
            top_n=max(1, min(limit, 50)),
            labeled_only=False,
        )
    return service.to_items(rows)


@router.get(
    "/{recommendation_id}/comparison/{other_id}",
    response_model=TradeComparisonResult,
)
def compare_recommendations(
    recommendation_id: int,
    other_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    """Compare two recommendations side by side."""
    if recommendation_id == other_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a recommendation to itself",
        )

    service = TradeComparisonService(db)
    result = service.compare_ids(recommendation_id, other_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both recommendations not found",
        )
    return result
