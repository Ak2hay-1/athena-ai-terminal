"""
MT5 Tick Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Tick Information
# ==========================================================

class MT5TickInfo(BaseModel):
    """
    MetaTrader 5 tick information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    symbol: str

    bid: Decimal

    ask: Decimal

    last: Decimal

    volume: Decimal

    time: datetime

    time_msc: int

    flags: int

    volume_real: Decimal


# ==========================================================
# Tick Request
# ==========================================================

class MT5TickRequest(BaseModel):
    """
    Request latest tick.
    """

    symbol: str = Field(
        min_length=1,
        max_length=32,
    )


# ==========================================================
# Multiple Tick Request
# ==========================================================

class MT5TickBatchRequest(BaseModel):
    """
    Request latest ticks.
    """

    symbols: list[str] = Field(
        min_length=1,
    )


# ==========================================================
# Tick History Request
# ==========================================================

class MT5TickHistoryRequest(BaseModel):
    """
    Historical tick request.
    """

    symbol: str

    from_time: datetime

    to_time: datetime


# ==========================================================
# Tick History Response
# ==========================================================

class MT5TickHistoryResponse(BaseModel):
    """
    Historical ticks.
    """

    symbol: str

    total: int

    ticks: list[MT5TickInfo]


# ==========================================================
# Live Tick
# ==========================================================

class MT5LiveTick(BaseModel):
    """
    WebSocket tick payload.
    """

    event: str = "tick"

    symbol: str

    tick: MT5TickInfo


# ==========================================================
# Tick Stream
# ==========================================================

class MT5TickStream(BaseModel):
    """
    Tick stream payload.
    """

    event: str = "ticks"

    timestamp: datetime

    ticks: list[MT5TickInfo]


# ==========================================================
# Tick Statistics
# ==========================================================

class MT5TickStatistics(BaseModel):
    """
    Tick statistics.
    """

    symbol: str

    first_tick: datetime | None

    last_tick: datetime | None

    total_ticks: int

    highest_bid: Decimal

    lowest_bid: Decimal

    highest_ask: Decimal

    lowest_ask: Decimal


# ==========================================================
# Spread Information
# ==========================================================

class MT5SpreadInfo(BaseModel):
    """
    Current spread information.
    """

    symbol: str

    bid: Decimal

    ask: Decimal

    spread_points: int

    spread_price: Decimal

    timestamp: datetime


# ==========================================================
# Tick Subscription
# ==========================================================

class MT5TickSubscription(BaseModel):
    """
    Subscribe or unsubscribe from tick streaming.
    """

    symbol: str

    subscribe: bool = True


# ==========================================================
# Tick Subscription Response
# ==========================================================

class MT5TickSubscriptionResponse(BaseModel):
    """
    Tick subscription response.
    """

    success: bool

    symbol: str

    message: str