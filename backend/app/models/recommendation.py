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
