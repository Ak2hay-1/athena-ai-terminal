"""
Market Schemas.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Base
# ==========================================================

class MarketCandleBase(BaseModel):
    """
    Base market candle schema.
    """

    symbol: str = Field(
        min_length=1,
        max_length=20,
        examples=["EURUSD"],
    )

    timeframe: str = Field(
        min_length=1,
        max_length=10,
        examples=["M15"],
    )

    time: datetime

    open: float

    high: float

    low: float

    close: float

    tick_volume: int = 0

    spread: int = 0

    real_volume: int = 0


# ==========================================================
# Create
# ==========================================================

class MarketCandleCreate(MarketCandleBase):
    """
    Create candle.
    """

    pass


# ==========================================================
# Update
# ==========================================================

class MarketCandleUpdate(BaseModel):
    """
    Update candle.
    """

    open: float | None = None

    high: float | None = None

    low: float | None = None

    close: float | None = None

    tick_volume: int | None = None

    spread: int | None = None

    real_volume: int | None = None


# ==========================================================
# Read
# ==========================================================

class MarketCandleRead(MarketCandleBase):
    """
    Market candle response.

    ``id`` / timestamps are present for DB-backed rows and optional when
    served from the multi-layer cache (chart consumers only need OHLCV).
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int = 0

    created_at: datetime | None = None

    updated_at: datetime | None = None

    body: float = 0.0

    range: float = 0.0

    is_bullish: bool = False

    is_bearish: bool = False

    def model_post_init(self, __context: object) -> None:
        object.__setattr__(self, "body", abs(self.close - self.open))
        object.__setattr__(self, "range", self.high - self.low)
        object.__setattr__(self, "is_bullish", self.close > self.open)
        object.__setattr__(self, "is_bearish", self.close < self.open)


# ==========================================================
# Query
# ==========================================================

class MarketQuery(BaseModel):
    """
    Market query parameters.
    """

    symbol: str

    timeframe: str

    limit: int = Field(
        default=500,
        ge=1,
        le=10000,
    )


# ==========================================================
# Time Range
# ==========================================================

class MarketHistoryRequest(BaseModel):
    """
    Historical candle request.
    """

    symbol: str

    timeframe: str

    start_time: datetime

    end_time: datetime


# ==========================================================
# Statistics
# ==========================================================

class MarketStatistics(BaseModel):
    """
    Market statistics.
    """

    symbol: str

    timeframe: str

    candle_count: int

    first_candle: datetime | None

    last_candle: datetime | None


# ==========================================================
# Backfill
# ==========================================================

class MarketBackfillRequest(BaseModel):
    """Deep history pull from MT5 into Postgres."""

    symbol: str = Field(min_length=1, max_length=20)
    timeframe: str = Field(min_length=1, max_length=10)
    count: int | None = Field(
        default=None,
        ge=1,
        description="Bars to request (capped by MARKET_BACKFILL_BARS).",
    )


class MarketBackfillResult(BaseModel):
    """Result of an MT5 → DB backfill."""

    symbol: str
    timeframe: str
    requested: int
    inserted: int
    candle_count: int
    oldest: datetime | None = None
    newest: datetime | None = None


# ==========================================================
# Quotes
# ==========================================================

class MarketQuote(BaseModel):
    """
    Live market quote (tick mid with candle fallback).
    """

    symbol: str

    bid: float

    ask: float

    mid: float

    time: datetime | None = None

    source: str = "tick"


# ==========================================================
# WebSocket
# ==========================================================

class LiveCandle(BaseModel):
    """
    Live candle payload.
    """

    symbol: str

    timeframe: str

    candle: MarketCandleRead