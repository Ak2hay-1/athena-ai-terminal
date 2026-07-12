"""
Market candle model.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class MarketCandle(BaseModel):
    """
    Stores historical and live market candles.
    """

    __tablename__ = "market_candles"

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

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    open: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    high: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    low: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    close: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    tick_volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    spread: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    real_volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_symbol_timeframe_time",
            "symbol",
            "timeframe",
            "time",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MarketCandle("
            f"{self.symbol} "
            f"{self.timeframe} "
            f"{self.time}"
            f")>"
        )