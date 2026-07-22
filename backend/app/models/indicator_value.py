"""
Indicator Value Model.

Persisted per-candle indicator snapshots. Written incrementally after
each candle close so startup and analytics never recalculate history.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class IndicatorValue(BaseModel):
    """Indicator values for one completed candle."""

    __tablename__ = "indicator_values"

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timeframe",
            "time",
            name="uq_indicator_value",
        ),
        Index(
            "idx_indicator_symbol_tf_time",
            "symbol",
            "timeframe",
            "time",
        ),
    )

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

    # Candle open time (UTC bucket start) the values belong to.
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # e.g. {"rsi_14": 55.2, "ema_20": 2411.5, "atr_14": 3.1, ...}
    values: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    indicator_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0",
    )

    def __repr__(self) -> str:
        return (
            f"<IndicatorValue({self.symbol} {self.timeframe} {self.time})>"
        )
