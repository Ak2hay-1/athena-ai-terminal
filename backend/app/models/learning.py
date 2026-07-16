"""
Learning and outcome tracking models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class OutcomeLabel(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    NEUTRAL = "NEUTRAL"


class RecommendationOutcome(BaseModel):
    """
    Labeled outcome for a past recommendation.
    """

    __tablename__ = "recommendation_outcomes"

    __table_args__ = (
        Index("idx_outcome_recommendation", "recommendation_id"),
    )

    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    predicted_signal: Mapped[str] = mapped_column(String(8), nullable=False)

    label: Mapped[str] = mapped_column(String(16), nullable=False)

    pnl_proxy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    horizon_candles: Mapped[int] = mapped_column(Integer, nullable=False)

    labeled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class PatternOccurrence(BaseModel):
    """
    Detected pattern with eventual outcome.
    """

    __tablename__ = "pattern_occurrences"

    __table_args__ = (
        Index("idx_pattern_symbol_tf", "symbol", "timeframe"),
    )

    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    pattern_type: Mapped[str] = mapped_column(String(64), nullable=False)

    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    outcome: Mapped[str | None] = mapped_column(String(16), nullable=True)


class ConfluenceSnapshot(BaseModel):
    """
    Confluence factor scores at decision time.
    """

    __tablename__ = "confluence_snapshots"

    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    factors: Mapped[dict] = mapped_column(JSONB, nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, nullable=False)


class ModelMetric(BaseModel):
    """
    Versioned model accuracy statistics.
    """

    __tablename__ = "model_metrics"

    model_version: Mapped[str] = mapped_column(String(64), nullable=False)

    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
