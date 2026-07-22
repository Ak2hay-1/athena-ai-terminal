"""
AI Models.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.core.enums import RecommendationSignal
from app.risk.models import ValidationFlags
from app.schemas.institutional import ChecklistItem
from app.schemas.institutional import ConfidenceBreakdown
from app.schemas.institutional import EntryZone
from app.schemas.institutional import MarketHeatmap
from app.schemas.probability import TradeProbabilityResult


class AIRecommendation(BaseModel):
    """
    Final recommendation produced by Athena.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )

    signal: RecommendationSignal = RecommendationSignal.HOLD

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    # Trading levels (always from risk engine)
    entry: float = 0.0

    entry_type: str = "NONE"

    stop_loss: float = 0.0

    take_profit: float = 0.0

    risk_reward: float = 0.0

    risk_pips: float = 0.0

    reward_pips: float = 0.0

    sl_reason: str = ""

    tp_reason: str = ""

    entry_reason: str = ""

    validation: ValidationFlags = Field(default_factory=ValidationFlags)

    confidence_breakdown: ConfidenceBreakdown | None = None

    institutional_checklist: list[ChecklistItem] = Field(default_factory=list)

    market_heatmap: MarketHeatmap | None = None

    entry_zone: EntryZone | None = None

    trade_probability: int = Field(default=0, ge=0, le=100)

    similar_trade_count: int = Field(default=0, ge=0)

    historical_win_rate: int = Field(default=0, ge=0, le=100)

    expected_rr: float = 0.0

    expected_hold_time: str = ""

    trade_quality: int = Field(default=0, ge=0, le=100)

    quality_grade: str = ""

    historical_insights: list[str] = Field(default_factory=list)

    probability_detail: TradeProbabilityResult | None = None

    # Narrative (AI or risk engine)
    reason: list[str] = Field(
        default_factory=list,
    )

    # Analysis metadata
    trend: str | None = None

    confluence: int | None = None

    timeframe: str | None = None

    symbol: str | None = None

    # Continuous learning audit (write-once)
    engine_version: str = "1.0.0"

    learning_version: str = "1.0.0"

    weight_version: str = "baseline"

    indicator_version: str = "1.0.0"

    strategy_version: str = "1.0.0"

    market_regime: str | None = None

    # Institutional qualification desk
    setup_quality: int = Field(default=0, ge=0, le=100)

    setup_quality_grade: str = ""

    setup_quality_components: dict = Field(default_factory=dict)

    scanner_group: str = ""

    lifecycle_state: str = "NEW"

    rejection_checklist: list[dict] = Field(default_factory=list)

    qualification_score: int = Field(default=0, ge=0, le=100)

    trend_strength: float = 0.0

    correlated: bool = False

    correlation_note: str = ""

    parent_recommendation_id: int | None = None
