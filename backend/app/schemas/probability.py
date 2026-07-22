"""
Deterministic trade probability / quality / comparison schemas.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class TradeProbabilityResult(BaseModel):
    """Estimated success probability from historical similar trades."""

    model_config = ConfigDict(extra="ignore")

    probability: int = Field(default=0, ge=0, le=100)
    confidence_category: str = "LOW_SAMPLE"
    similar_trades: int = Field(default=0, ge=0)
    historical_win_rate: int = Field(default=0, ge=0, le=100)
    expected_rr: float = 0.0
    expected_hold_time: str = ""
    historical_average_profit: float = 0.0
    historical_average_loss: float = 0.0


class TradeQualityResult(BaseModel):
    """Institutional trade quality score."""

    model_config = ConfigDict(extra="ignore")

    trade_quality: int = Field(default=0, ge=0, le=100)
    grade: str = "D"


class SimilarRecommendationItem(BaseModel):
    """One historically similar recommendation."""

    model_config = ConfigDict(extra="ignore")

    id: int
    symbol: str
    timeframe: str
    signal: str
    confidence: int = 0
    trend: str = ""
    risk_reward: float = 0.0
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    outcome_label: str | None = None
    pnl_proxy: float | None = None
    trade_probability: int | None = None
    trade_quality: int | None = None
    quality_grade: str | None = None
    created_at: str | None = None


class MetricComparison(BaseModel):
    """Side-by-side metric with optional winner."""

    model_config = ConfigDict(extra="ignore")

    a: str | int | float | None = None
    b: str | int | float | None = None
    winner: str | None = None


class TradeComparisonResult(BaseModel):
    """Comparison of two recommendations."""

    model_config = ConfigDict(extra="ignore")

    winner: str = "TIE"
    comparison: dict[str, MetricComparison] = Field(default_factory=dict)
