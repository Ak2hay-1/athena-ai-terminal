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
from sqlalchemy.types import JSON

from app.models.base_model import BaseModel


class OutcomeLabel(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    NEUTRAL = "NEUTRAL"


class OutcomeResult(str, Enum):
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    MANUAL_EXIT = "MANUAL_EXIT"
    TIMEOUT = "TIMEOUT"
    NEUTRAL = "NEUTRAL"


class RecommendationOutcome(BaseModel):
    """Labeled outcome for a past recommendation."""

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

    result: Mapped[str | None] = mapped_column(String(16), nullable=True)

    entry: Mapped[float | None] = mapped_column(Float, nullable=True)

    sl: Mapped[float | None] = mapped_column(Float, nullable=True)

    tp: Mapped[float | None] = mapped_column(Float, nullable=True)

    rr: Mapped[float | None] = mapped_column(Float, nullable=True)

    profit: Mapped[float | None] = mapped_column(Float, nullable=True)

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    regime: Mapped[str | None] = mapped_column(String(32), nullable=True)

    confidence_at_entry: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PatternOccurrence(BaseModel):
    """Detected pattern with eventual outcome."""

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
    """Confluence factor scores at decision time."""

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
    """Versioned model accuracy statistics."""

    __tablename__ = "model_metrics"

    model_version: Mapped[str] = mapped_column(String(64), nullable=False)

    symbol: Mapped[str] = mapped_column(String(16), nullable=False)

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)

    accuracy: Mapped[float] = mapped_column(Float, nullable=False)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FeatureStatistic(BaseModel):
    __tablename__ = "feature_statistics"

    feature_key: Mapped[str] = mapped_column(String(64), nullable=False)

    symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)

    timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)

    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_rr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class SymbolStatistic(BaseModel):
    __tablename__ = "symbol_statistics"

    symbol: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_rr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class TimeframeStatistic(BaseModel):
    __tablename__ = "timeframe_statistics"

    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_rr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    trade_frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class StrategyStatistic(BaseModel):
    __tablename__ = "strategy_statistics"

    combo_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_rr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class RegimeStatistic(BaseModel):
    __tablename__ = "regime_statistics"

    regime: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    avg_rr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ConfidenceCalibration(BaseModel):
    __tablename__ = "confidence_calibration"

    bucket: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    predicted_mid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    actual_win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LearningVersion(BaseModel):
    __tablename__ = "learning_versions"

    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WeightHistory(BaseModel):
    __tablename__ = "weight_history"

    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    weights: Mapped[dict] = mapped_column(JSON, nullable=False)

    learning_version: Mapped[str] = mapped_column(String(64), nullable=False)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
