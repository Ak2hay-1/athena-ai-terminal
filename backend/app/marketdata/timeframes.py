"""
Timeframe definitions and UTC bucket math.

Every candle timestamp represents the candle OPEN time of its UTC
bucket. Bucket boundaries are determined by time alone — never by UI
refreshes, restarts, or reconnects.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

# Duration of each supported timeframe in seconds.
TIMEFRAME_SECONDS: dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}

SUPPORTED_TIMEFRAMES: tuple[str, ...] = tuple(TIMEFRAME_SECONDS)


def timeframe_seconds(timeframe: str) -> int:
    """Return the bucket duration in seconds for a timeframe."""

    try:
        return TIMEFRAME_SECONDS[timeframe.upper()]
    except KeyError:
        raise ValueError(f"Unsupported timeframe: {timeframe}") from None


def bucket_start_epoch(epoch_seconds: float, timeframe: str) -> int:
    """Return the UTC bucket open time (epoch seconds) for a moment."""

    duration = timeframe_seconds(timeframe)
    epoch = int(epoch_seconds)
    return epoch - (epoch % duration)


def bucket_end_epoch(epoch_seconds: float, timeframe: str) -> int:
    """Return the exclusive UTC bucket end time (epoch seconds)."""

    return bucket_start_epoch(epoch_seconds, timeframe) + timeframe_seconds(
        timeframe
    )


def bucket_start_datetime(moment: datetime, timeframe: str) -> datetime:
    """Return the UTC bucket open time for an aware datetime."""

    return epoch_to_datetime(
        bucket_start_epoch(moment.timestamp(), timeframe)
    )


def is_same_bucket(a: float, b: float, timeframe: str) -> bool:
    """True when two epoch timestamps fall inside the same bucket."""

    return bucket_start_epoch(a, timeframe) == bucket_start_epoch(
        b, timeframe
    )


def epoch_to_datetime(epoch_seconds: float) -> datetime:
    """Convert epoch seconds to an aware UTC datetime."""

    return datetime.fromtimestamp(epoch_seconds, tz=UTC)


def to_utc(moment: datetime) -> datetime:
    """Coerce a datetime to aware UTC (naive treated as UTC)."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)
