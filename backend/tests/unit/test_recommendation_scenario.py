"""Best-across-timeframes scenario selection."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from types import SimpleNamespace

from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection
from app.repositories.recommendation_repository import RecommendationRepository


def _row(
    *,
    timeframe: str,
    signal: RecommendationSignal,
    confidence: int,
    confluence: int = 50,
    trade_quality: int = 50,
    created_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        timeframe=timeframe,
        signal=signal,
        confidence=confidence,
        confluence=confluence,
        trade_quality=trade_quality,
        created_at=created_at or datetime(2026, 7, 22, tzinfo=timezone.utc),
        trend=TrendDirection.BULLISH,
        id=1,
    )


def test_prefers_actionable_over_hold_even_if_lower_confidence() -> None:
    hold = _row(timeframe="M5", signal=RecommendationSignal.HOLD, confidence=90)
    buy = _row(timeframe="M15", signal=RecommendationSignal.BUY, confidence=70)
    best = max([hold, buy], key=RecommendationRepository._scenario_sort_key)
    assert best.timeframe == "M15"
    assert best.signal == RecommendationSignal.BUY


def test_among_actionable_prefers_higher_confidence() -> None:
    m5 = _row(timeframe="M5", signal=RecommendationSignal.BUY, confidence=65)
    m15 = _row(timeframe="M15", signal=RecommendationSignal.BUY, confidence=82)
    best = max([m5, m15], key=RecommendationRepository._scenario_sort_key)
    assert best.timeframe == "M15"


def test_tie_break_prefers_higher_timeframe() -> None:
    m5 = _row(timeframe="M5", signal=RecommendationSignal.BUY, confidence=80)
    h1 = _row(timeframe="H1", signal=RecommendationSignal.BUY, confidence=80)
    best = max([m5, h1], key=RecommendationRepository._scenario_sort_key)
    assert best.timeframe == "H1"
