"""
Recommendation Model.

Stores AI-generated market recommendations.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint
from sqlalchemy import Enum
from sqlalchemy import Index
from sqlalchemy import JSON
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection
from app.models.base_model import BaseModel


class Recommendation(BaseModel):
    """
    AI recommendation snapshot.
    """

    __tablename__ = "recommendations"

    __table_args__ = (
        Index(
            "idx_recommendation_symbol",
            "symbol",
        ),
        Index(
            "idx_recommendation_timeframe",
            "timeframe",
        ),
        Index(
            "idx_recommendation_symbol_timeframe",
            "symbol",
            "timeframe",
        ),
        Index(
            "idx_recommendation_symbol_tf_signal_created",
            "symbol",
            "timeframe",
            "signal",
            "created_at",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 100",
            name="ck_recommendation_confidence",
        ),
        CheckConstraint(
            "confluence >= 0 AND confluence <= 100",
            name="ck_recommendation_confluence",
        ),
    )

    # ==========================================================
    # Instrument
    # ==========================================================

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    timeframe: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # Recommendation
    # ==========================================================

    signal: Mapped[RecommendationSignal] = mapped_column(
        Enum(
            RecommendationSignal,
            name="recommendation_signal",
        ),
        nullable=False,
    )

    confidence: Mapped[int] = mapped_column(
        nullable=False,
    )

    trend: Mapped[TrendDirection] = mapped_column(
        Enum(
            TrendDirection,
            name="trend_direction",
        ),
        nullable=False,
    )

    confluence: Mapped[int] = mapped_column(
        nullable=False,
    )

    # ==========================================================
    # Trading Levels
    # ==========================================================

    entry_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    stop_loss: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    take_profit: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    risk_reward: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    entry_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="NONE",
        server_default="NONE",
    )

    risk_pips: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    reward_pips: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    sl_reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        server_default="",
    )

    tp_reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        server_default="",
    )

    validation: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    confidence_breakdown: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    institutional_checklist: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    market_heatmap: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    entry_zone: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ==========================================================
    # Trade Probability (deterministic)
    # ==========================================================

    trade_probability: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    similar_trade_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    historical_win_rate: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    expected_rr: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )

    expected_hold_time: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
        server_default="",
    )

    trade_quality: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    quality_grade: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="",
        server_default="",
    )

    historical_insights: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    probability_detail: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # ==========================================================
    # AI Details
    # ==========================================================

    analysis: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    reasoning: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ==========================================================
    # Continuous Learning audit (write-once at create)
    # ==========================================================

    engine_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
    )

    learning_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
    )

    weight_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="baseline",
        server_default="baseline",
    )

    indicator_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
    )

    strategy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
    )

    market_regime: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # ==========================================================
    # Institutional qualification desk
    # ==========================================================

    setup_quality: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    setup_quality_grade: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="",
        server_default="",
    )

    setup_quality_components: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    scanner_group: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="no_trade",
        server_default="no_trade",
    )

    lifecycle_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="NEW",
        server_default="NEW",
        index=True,
    )

    rejection_checklist: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    qualification_score: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    trend_strength: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
        server_default="0",
    )

    correlated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    correlation_note: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        server_default="",
    )

    parent_recommendation_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    @property
    def is_buy(self) -> bool:
        """Return True if recommendation is BUY."""
        return self.signal == RecommendationSignal.BUY

    @property
    def is_sell(self) -> bool:
        """Return True if recommendation is SELL."""
        return self.signal == RecommendationSignal.SELL

    @property
    def is_hold(self) -> bool:
        """Return True if recommendation is HOLD."""
        return self.signal == RecommendationSignal.HOLD

    @property
    def is_no_trade(self) -> bool:
        """Return True if recommendation is NO_TRADE."""
        return self.signal == RecommendationSignal.NO_TRADE

    @property
    def is_high_confidence(self) -> bool:
        """Return True if confidence is at least 80%."""
        return self.confidence >= 80

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"{self.signal.value} "
            f"{self.symbol} "
            f"{self.timeframe} "
            f"({self.confidence}%)"
        )

    def __repr__(self) -> str:
        return (
            f"<Recommendation("
            f"{self.symbol} "
            f"{self.timeframe} "
            f"{self.signal.value} "
            f"{self.confidence:.2f}"
            f")>"
        )
