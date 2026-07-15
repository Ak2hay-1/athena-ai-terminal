"""
Schema package exports.
"""

from app.schemas.market import (
    LiveCandle,
    MarketCandleCreate,
    MarketCandleRead,
    MarketCandleUpdate,
    MarketHistoryRequest,
    MarketQuery,
    MarketStatistics,
)

from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationQuery,
    RecommendationRead,
)

__all__ = [
    # Market
    "MarketCandleCreate",
    "MarketCandleRead",
    "MarketCandleUpdate",
    "MarketQuery",
    "MarketHistoryRequest",
    "MarketStatistics",
    "LiveCandle",

    # Recommendation
    "RecommendationCreate",
    "RecommendationQuery",
    "RecommendationRead",
]
