"""
Adaptive confluence weighting based on historical accuracy.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.learning.pattern_statistics import PatternStatistics


DEFAULT_WEIGHTS = {
    "ema": 1.0,
    "rsi": 1.0,
    "macd": 1.0,
    "bos": 1.0,
    "choch": 1.0,
    "fvg": 1.0,
    "order_block": 1.0,
    "news": 1.0,
}


class AdaptiveWeightEngine:
    """
    Adjust factor weights using observed pattern performance.
    """

    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self._cache: dict[str, dict[str, float]] = {}

    def get_weights(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, float]:
        if not settings.LEARNING_ENABLED or self.db is None:
            return DEFAULT_WEIGHTS.copy()

        cache_key = f"{symbol}:{timeframe}"

        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        stats = PatternStatistics(self.db).win_rates(
            symbol,
            timeframe,
        )

        weights = DEFAULT_WEIGHTS.copy()

        mapping = {
            "BOS": "bos",
            "CHOCH": "choch",
            "FVG": "fvg",
            "ORDER_BLOCK": "order_block",
        }

        for pattern, rate in stats.items():
            key = mapping.get(pattern.upper())

            if key:
                weights[key] = 0.5 + rate

        self._cache[cache_key] = weights
        return weights.copy()

    def clear_cache(self) -> None:
        self._cache.clear()
