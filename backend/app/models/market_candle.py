"""
Market Candle Model.

Stores historical OHLCV market data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class MarketCandle(BaseModel):
    """
    Historical market candle.
    """

    __tablename__ = "market_candles"

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "timeframe",
            "time",
            name="uq_market_candle",
        ),
        Index(
            "idx_market_symbol",
            "symbol",
        ),
        Index(
            "idx_market_timeframe",
            "timeframe",
        ),
        Index(
            "idx_market_time",
            "time",
        ),
        Index(
            "idx_market_symbol_time",
            "symbol",
            "time",
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
    # Candle
    # ==========================================================

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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

    # ==========================================================
    # Volume
    # ==========================================================

    tick_volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    spread: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    real_volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    # ==========================================================
    # Helpers
    # ==========================================================

    @property
    def body(self) -> float:
        """
        Candle body size.
        """
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        """
        Total candle range.
        """
        return self.high - self.low

    @property
    def is_bullish(self) -> bool:
        """
        Bullish candle.
        """
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """
        Bearish candle.
        """
        return self.close < self.open

    def __repr__(self) -> str:
        return (
            f"<MarketCandle("
            f"{self.symbol} "
            f"{self.timeframe} "
            f"{self.time}"
            f")>"
        )