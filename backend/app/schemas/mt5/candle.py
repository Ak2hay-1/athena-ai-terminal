"""
MT5 Candle Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Timeframes
# ==========================================================

class MT5Timeframe(str, Enum):
    """
    MetaTrader 5 supported timeframes.
    """

    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    M10 = "M10"
    M12 = "M12"
    M15 = "M15"
    M20 = "M20"
    M30 = "M30"

    H1 = "H1"
    H2 = "H2"
    H3 = "H3"
    H4 = "H4"
    H6 = "H6"
    H8 = "H8"
    H12 = "H12"

    D1 = "D1"

    W1 = "W1"

    MN1 = "MN1"


# ==========================================================
# Candle
# ==========================================================

class MT5Candle(BaseModel):
    """
    MT5 candle.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    symbol: str

    timeframe: MT5Timeframe

    time: datetime

    open: Decimal

    high: Decimal

    low: Decimal

    close: Decimal

    tick_volume: int

    spread: int

    real_volume: int


# ==========================================================
# Download Request
# ==========================================================

class MT5CandleRequest(BaseModel):
    """
    Historical candle request.
    """

    symbol: str

    timeframe: MT5Timeframe

    count: int = Field(
        default=500,
        ge=1,
        le=100000,
    )


# ==========================================================
# Date Range Request
# ==========================================================

class MT5CandleRangeRequest(BaseModel):
    """
    Historical candle range.
    """

    symbol: str

    timeframe: MT5Timeframe

    from_time: datetime

    to_time: datetime


# ==========================================================
# Download Response
# ==========================================================

class MT5CandleResponse(BaseModel):
    """
    Candle download response.
    """

    symbol: str

    timeframe: MT5Timeframe

    total: int

    candles: list[MT5Candle]


# ==========================================================
# Latest Candle
# ==========================================================

class MT5LatestCandle(BaseModel):
    """
    Latest candle.
    """

    symbol: str

    timeframe: MT5Timeframe

    candle: MT5Candle


# ==========================================================
# Live Candle
# ==========================================================

class MT5LiveCandle(BaseModel):
    """
    WebSocket candle.
    """

    event: str = "candle"

    symbol: str

    timeframe: MT5Timeframe

    candle: MT5Candle


# ==========================================================
# Bulk Import
# ==========================================================

class MT5BulkCandleImport(BaseModel):
    """
    Bulk candle import.
    """

    symbol: str

    timeframe: MT5Timeframe

    candles: list[MT5Candle]


# ==========================================================
# Synchronization
# ==========================================================

class MT5CandleSync(BaseModel):
    """
    Candle synchronization result.
    """

    symbol: str

    timeframe: MT5Timeframe

    downloaded: int

    inserted: int

    skipped: int

    duplicates: int

    started_at: datetime

    completed_at: datetime


# ==========================================================
# Statistics
# ==========================================================

class MT5CandleStatistics(BaseModel):
    """
    Candle statistics.
    """

    symbol: str

    timeframe: MT5Timeframe

    first_candle: datetime | None

    last_candle: datetime | None

    total: int


# ==========================================================
# Collector Status
# ==========================================================

class MT5CollectorStatus(BaseModel):
    """
    Candle collector status.
    """

    running: bool

    symbol: str | None = None

    timeframe: MT5Timeframe | None = None

    last_update: datetime | None = None

    candles_processed: int

    message: str