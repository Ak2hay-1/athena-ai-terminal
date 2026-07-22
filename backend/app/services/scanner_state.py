"""
In-memory scanner state: Market Watch urgency cache + last scan timestamp.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any

# Change types that boost scanner urgency
URGENT_CHANGE_TYPES: frozenset[str] = frozenset(
    {
        "breakout",
        "breakdown",
        "volume_spike",
        "level_cross",
        "atr_expansion",
        "volatility_spike",
        "gap_detected",
        "swing_high",
        "swing_low",
        "trend_changed",
    }
)

# Higher = stronger boost
_CHANGE_WEIGHTS: dict[str, float] = {
    "breakout": 12.0,
    "breakdown": 12.0,
    "level_cross": 10.0,
    "volume_spike": 9.0,
    "gap_detected": 8.0,
    "atr_expansion": 7.0,
    "volatility_spike": 7.0,
    "trend_changed": 8.0,
    "swing_high": 6.0,
    "swing_low": 6.0,
}


@dataclass
class MarketWatchEvent:
    symbol: str
    timeframe: str
    change_type: str
    timestamp: datetime
    price: float | None = None
    extras: dict[str, Any] | None = None

    @property
    def weight(self) -> float:
        return _CHANGE_WEIGHTS.get(self.change_type, 4.0)


class ScannerStateStore:
    """Process-local Market Watch event cache for scanner ranking."""

    def __init__(self, *, max_events: int = 2000) -> None:
        self._lock = threading.RLock()
        self._events: OrderedDict[str, MarketWatchEvent] = OrderedDict()
        self._max_events = max_events
        self.last_market_watch_scan_at: datetime | None = None
        self.last_scan_universe_size: int = 0

    @staticmethod
    def _key(symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}|{timeframe.upper()}"

    def record_market_watch(
        self,
        *,
        symbol: str,
        timeframe: str,
        change_type: str,
        price: float | None = None,
        extras: dict[str, Any] | None = None,
        at: datetime | None = None,
    ) -> MarketWatchEvent | None:
        change_type = str(change_type).lower().strip()
        if change_type not in URGENT_CHANGE_TYPES:
            return None

        event = MarketWatchEvent(
            symbol=symbol.upper(),
            timeframe=timeframe.upper(),
            change_type=change_type,
            timestamp=at or datetime.now(timezone.utc),
            price=price,
            extras=extras or {},
        )
        key = self._key(event.symbol, event.timeframe)
        with self._lock:
            # Prefer stronger / newer events for the same pair
            existing = self._events.get(key)
            if existing is not None and existing.weight > event.weight:
                # Keep stronger event if still fresh; bump timestamp lightly
                if (event.timestamp - existing.timestamp).total_seconds() < 120:
                    return existing
            self._events[key] = event
            self._events.move_to_end(key)
            while len(self._events) > self._max_events:
                self._events.popitem(last=False)
        return event

    def get_event(
        self,
        symbol: str,
        timeframe: str,
        *,
        max_age_seconds: int = 300,
    ) -> MarketWatchEvent | None:
        key = self._key(symbol, timeframe)
        now = datetime.now(timezone.utc)
        with self._lock:
            event = self._events.get(key)
            if event is None:
                return None
            age = (now - event.timestamp).total_seconds()
            if age > max_age_seconds:
                return None
            return event

    def mark_scan(
        self,
        *,
        at: datetime | None = None,
        universe_size: int = 0,
    ) -> None:
        with self._lock:
            self.last_market_watch_scan_at = at or datetime.now(timezone.utc)
            self.last_scan_universe_size = universe_size

    def snapshot_meta(self) -> dict[str, Any]:
        with self._lock:
            return {
                "last_market_watch_scan_at": self.last_market_watch_scan_at,
                "universe_size": self.last_scan_universe_size,
            }


scanner_state = ScannerStateStore()
