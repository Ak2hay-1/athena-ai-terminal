"""
Recommendation Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection
from app.risk.models import ValidationFlags
from app.schemas.institutional import ChecklistItem
from app.schemas.institutional import ConfidenceBreakdown
from app.schemas.institutional import EntryZone
from app.schemas.institutional import MarketHeatmap
from app.schemas.probability import TradeProbabilityResult


# ==========================================================
# Base
# ==========================================================

class RecommendationBase(BaseModel):
    """
    Base recommendation schema.
    """

    symbol: str = Field(
        min_length=1,
        max_length=20,
    )

    timeframe: str = Field(
        min_length=1,
        max_length=10,
    )

    signal: RecommendationSignal

    confidence: int = Field(
        ge=0,
        le=100,
    )

    trend: TrendDirection

    confluence: int = Field(
        ge=0,
        le=100,
    )

    entry_price: Decimal

    stop_loss: Decimal

    take_profit: Decimal

    risk_reward: Decimal

    entry_type: str = "NONE"

    risk_pips: Decimal = Decimal("0")

    reward_pips: Decimal = Decimal("0")

    sl_reason: str = ""

    tp_reason: str = ""

    validation: ValidationFlags = Field(default_factory=ValidationFlags)

    confidence_breakdown: ConfidenceBreakdown | None = None

    institutional_checklist: list[ChecklistItem] = Field(default_factory=list)

    market_heatmap: MarketHeatmap | None = None

    entry_zone: EntryZone | None = None

    trade_probability: int = Field(default=0, ge=0, le=100)

    similar_trade_count: int = Field(default=0, ge=0)

    historical_win_rate: int = Field(default=0, ge=0, le=100)

    expected_rr: Decimal = Decimal("0")

    expected_hold_time: str = ""

    trade_quality: int = Field(default=0, ge=0, le=100)

    quality_grade: str = ""

    historical_insights: list[str] = Field(default_factory=list)

    probability_detail: TradeProbabilityResult | None = None

    setup_quality: int = Field(default=0, ge=0, le=100)

    setup_quality_grade: str = ""

    setup_quality_components: dict[str, Any] = Field(default_factory=dict)

    scanner_group: str = "no_trade"

    lifecycle_state: str = "NEW"

    rejection_checklist: list[dict[str, Any]] = Field(default_factory=list)

    qualification_score: int = Field(default=0, ge=0, le=100)

    trend_strength: float = 0.0

    correlated: bool = False

    correlation_note: str = ""

    parent_recommendation_id: int | None = None

    market_regime: str | None = None

    analysis: dict[str, Any]

    reasoning: list[str]


# ==========================================================
# Create
# ==========================================================

class RecommendationCreate(RecommendationBase):
    """
    Create recommendation.
    """

    pass


# ==========================================================
# Read
# ==========================================================

class RecommendationRead(RecommendationBase):
    """
    Recommendation response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Query
# ==========================================================

class RecommendationQuery(BaseModel):
    """
    Recommendation query.
    """

    symbol: str

    timeframe: str | None = None

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )


class TimeframeSignalSnapshot(BaseModel):
    """Latest signal snapshot for one timeframe (scenario strip)."""

    model_config = ConfigDict(from_attributes=True)

    timeframe: str
    signal: RecommendationSignal
    confidence: int = Field(ge=0, le=100)
    trend: TrendDirection
    confluence: int = Field(default=0, ge=0, le=100)
    recommendation_id: int | None = None
    created_at: datetime | None = None


class SymbolScenarioRead(BaseModel):
    """
    Overall trade scenario for a symbol across timeframes.
    """

    symbol: str
    best: RecommendationRead | None = None
    by_timeframe: list[TimeframeSignalSnapshot] = Field(default_factory=list)
