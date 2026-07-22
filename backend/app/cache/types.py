"""Shared cache types.

Candles are stored as compact tuples to keep RAM usage predictable:

    (epoch_seconds, open, high, low, close, tick_volume, spread, real_volume)

Forming (live) candles are NEVER stored in historical series caches.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from typing import Any
from typing import TypedDict

# Compact on-wire / in-RAM bar representation.
CandleTuple = tuple[int, float, float, float, float, int, int, int]


class CandleDict(TypedDict):
    symbol: str
    timeframe: str
    time: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


def epoch_from_datetime(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def datetime_from_epoch(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch, tz=UTC)


def candle_to_tuple(
    *,
    time: datetime | int | float | str,
    open_: float,
    high: float,
    low: float,
    close: float,
    tick_volume: int = 0,
    spread: int = 0,
    real_volume: int = 0,
) -> CandleTuple:
    if isinstance(time, datetime):
        epoch = epoch_from_datetime(time)
    elif isinstance(time, str):
        parsed = datetime.fromisoformat(time.replace("Z", "+00:00"))
        epoch = epoch_from_datetime(parsed)
    else:
        epoch = int(time)

    return (
        epoch,
        float(open_),
        float(high),
        float(low),
        float(close),
        int(tick_volume or 0),
        int(spread or 0),
        int(real_volume or 0),
    )


def model_to_tuple(candle: Any) -> CandleTuple:
    """Convert ORM / pydantic / dict candle to compact tuple."""

    if isinstance(candle, (tuple, list)) and len(candle) >= 5:
        return candle_to_tuple(
            time=candle[0],
            open_=candle[1],
            high=candle[2],
            low=candle[3],
            close=candle[4],
            tick_volume=candle[5] if len(candle) > 5 else 0,
            spread=candle[6] if len(candle) > 6 else 0,
            real_volume=candle[7] if len(candle) > 7 else 0,
        )

    if isinstance(candle, dict):
        return candle_to_tuple(
            time=candle["time"],
            open_=candle["open"],
            high=candle["high"],
            low=candle["low"],
            close=candle["close"],
            tick_volume=candle.get("tick_volume", 0),
            spread=candle.get("spread", 0),
            real_volume=candle.get("real_volume", 0),
        )

    return candle_to_tuple(
        time=candle.time,
        open_=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        tick_volume=getattr(candle, "tick_volume", 0),
        spread=getattr(candle, "spread", 0),
        real_volume=getattr(candle, "real_volume", 0),
    )


def tuple_to_dict(
    bar: CandleTuple,
    *,
    symbol: str,
    timeframe: str,
) -> CandleDict:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "time": datetime_from_epoch(bar[0]).isoformat(),
        "open": bar[1],
        "high": bar[2],
        "low": bar[3],
        "close": bar[4],
        "tick_volume": bar[5],
        "spread": bar[6],
        "real_volume": bar[7],
    }


# Approximate bytes per stored bar (tuple of primitives + overhead).
BYTES_PER_CANDLE = 96
