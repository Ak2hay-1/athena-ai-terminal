"""
Short-lived AI market context cache (30–60s).

Caches summaries such as market structure, trend state, indicator
summary, and news summary. Invalidated on new candle, timeframe change,
or major market events.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from app.cache.logging_utils import cache_log


@dataclass
class _AiEntry:
    payload: dict[str, Any]
    expires_at: float
    candle_epoch: int | None = None


class AiContextCache:
    """Thread-safe TTL cache for AI context payloads."""

    def __init__(self, *, ttl_seconds: float = 45.0) -> None:
        self.ttl_seconds = max(5.0, float(ttl_seconds))
        self._entries: dict[str, _AiEntry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}:{timeframe.upper()}"

    def get(self, symbol: str, timeframe: str) -> dict[str, Any] | None:
        key = self._key(symbol, timeframe)
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._entries.pop(key, None)
                return None
            return dict(entry.payload)

    def set(
        self,
        symbol: str,
        timeframe: str,
        payload: dict[str, Any],
        *,
        candle_epoch: int | None = None,
        ttl_seconds: float | None = None,
    ) -> None:
        key = self._key(symbol, timeframe)
        ttl = self.ttl_seconds if ttl_seconds is None else max(5.0, ttl_seconds)
        with self._lock:
            self._entries[key] = _AiEntry(
                payload=dict(payload),
                expires_at=time.monotonic() + ttl,
                candle_epoch=candle_epoch,
            )

    def invalidate(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        *,
        reason: str = "manual",
    ) -> int:
        with self._lock:
            if symbol is None and timeframe is None:
                count = len(self._entries)
                self._entries.clear()
                if count:
                    cache_log("CACHE INVALIDATED", scope="ai", reason=reason)
                return count

            targets = []
            for key in list(self._entries.keys()):
                sym, tf = key.split(":", 1)
                if symbol and sym != symbol.upper():
                    continue
                if timeframe and tf != timeframe.upper():
                    continue
                targets.append(key)
            for key in targets:
                self._entries.pop(key, None)
            if targets:
                cache_log(
                    "CACHE INVALIDATED",
                    scope="ai",
                    reason=reason,
                    count=len(targets),
                )
            return len(targets)

    def invalidate_on_candle(
        self,
        symbol: str,
        timeframe: str,
        candle_epoch: int,
    ) -> None:
        """Drop AI context when a new candle closes for this series."""

        key = self._key(symbol, timeframe)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return
            if entry.candle_epoch is None or entry.candle_epoch < candle_epoch:
                self._entries.pop(key, None)
                cache_log(
                    "CACHE INVALIDATED",
                    scope="ai",
                    reason="new_candle",
                    symbol=symbol,
                    timeframe=timeframe,
                )

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"entries": len(self._entries)}
