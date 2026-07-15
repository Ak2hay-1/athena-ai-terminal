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
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime

    body: float

    range: float

    is_bullish: bool

    is_bearish: bool


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
# WebSocket
# ==========================================================

class LiveCandle(BaseModel):
    """
    Live candle payload.
    """

    symbol: str

    timeframe: str

    candle: MarketCandleRead