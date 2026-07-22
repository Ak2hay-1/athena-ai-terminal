"""
Layer 1 – RAM Cache.

Ultra-fast LRU series store for active charts:

- Recent candles (last N per symbol/timeframe)
- Indicator series snapshots
- Symbol metadata
- Chart viewport hints
- Short-lived AI market context (delegated TTL elsewhere)

Never stores live account information (positions, orders, margin,
balance, equity) or permanent live forming candles.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from app.cache.logging_utils import cache_log
from app.cache.types import BYTES_PER_CANDLE
from app.cache.types import CandleTuple


@dataclass
class SeriesEntry:
    """One symbol/timeframe candle series in RAM."""

    candles: list[CandleTuple] = field(default_factory=list)
    last_access: float = field(default_factory=time.monotonic)
    version: int = 0


@dataclass
class IndicatorEntry:
    """Cached indicator payload for a series fingerprint."""

    fingerprint: str
    values: dict[str, Any]
    last_access: float = field(default_factory=time.monotonic)


class RamCache:
    """
    Thread-safe LRU cache with configurable candle depth and memory cap.

    Eviction order:
        1. Inactive symbols past ``inactive_ttl_seconds``
        2. Least-recently-used series when over max candles / memory
    """

    def __init__(
        self,
        *,
        max_candles_per_series: int = 5000,
        max_memory_mb: float = 256.0,
        inactive_ttl_seconds: float = 900.0,
        max_series: int = 128,
    ) -> None:
        self.max_candles_per_series = max(1, int(max_candles_per_series))
        self.max_memory_bytes = max(16.0, float(max_memory_mb)) * 1024 * 1024
        self.inactive_ttl_seconds = max(1.0, float(inactive_ttl_seconds))
        self.max_series = max(1, int(max_series))

        self._series: OrderedDict[str, SeriesEntry] = OrderedDict()
        self._indicators: OrderedDict[str, IndicatorEntry] = OrderedDict()
        self._metadata: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._viewports: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def series_key(symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}:{timeframe.upper()}"

    # ------------------------------------------------------------------
    # Candle series
    # ------------------------------------------------------------------

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int | None = None,
        before_epoch: int | None = None,
    ) -> list[CandleTuple] | None:
        key = self.series_key(symbol, timeframe)
        with self._lock:
            entry = self._series.get(key)
            if entry is None or not entry.candles:
                return None

            entry.last_access = time.monotonic()
            self._series.move_to_end(key)

            candles = entry.candles
            if before_epoch is not None:
                candles = [c for c in candles if c[0] < before_epoch]
                if not candles:
                    return None

            if limit is not None and limit > 0:
                candles = candles[-limit:]
            return list(candles)

    def put_candles(
        self,
        symbol: str,
        timeframe: str,
        candles: list[CandleTuple],
        *,
        replace: bool = True,
    ) -> None:
        if not candles:
            return

        key = self.series_key(symbol, timeframe)
        with self._lock:
            if replace:
                merged = self._dedupe_sort(candles)
            else:
                existing = self._series.get(key)
                base = list(existing.candles) if existing else []
                merged = self._dedupe_sort(base + candles)

            if len(merged) > self.max_candles_per_series:
                merged = merged[-self.max_candles_per_series :]

            entry = self._series.get(key)
            if entry is None:
                entry = SeriesEntry()
                self._series[key] = entry
            entry.candles = merged
            entry.last_access = time.monotonic()
            entry.version += 1
            self._series.move_to_end(key)
            self._enforce_limits()

    def append_closed_candle(
        self,
        symbol: str,
        timeframe: str,
        candle: CandleTuple,
    ) -> None:
        """
        Append or replace a *completed* candle.

        Forming candles must not be passed here.
        """

        key = self.series_key(symbol, timeframe)
        with self._lock:
            entry = self._series.get(key)
            if entry is None:
                entry = SeriesEntry(candles=[candle])
                self._series[key] = entry
            else:
                if entry.candles and entry.candles[-1][0] == candle[0]:
                    entry.candles[-1] = candle
                elif entry.candles and entry.candles[-1][0] > candle[0]:
                    # Out-of-order closed bar — merge properly.
                    entry.candles = self._dedupe_sort(
                        entry.candles + [candle]
                    )
                else:
                    entry.candles.append(candle)
                    if len(entry.candles) > self.max_candles_per_series:
                        entry.candles = entry.candles[
                            -self.max_candles_per_series :
                        ]
                entry.version += 1
                entry.last_access = time.monotonic()
                self._series.move_to_end(key)
            self._enforce_limits()

    def newest_epoch(self, symbol: str, timeframe: str) -> int | None:
        key = self.series_key(symbol, timeframe)
        with self._lock:
            entry = self._series.get(key)
            if entry is None or not entry.candles:
                return None
            return entry.candles[-1][0]

    def series_version(self, symbol: str, timeframe: str) -> int:
        key = self.series_key(symbol, timeframe)
        with self._lock:
            entry = self._series.get(key)
            return entry.version if entry else 0

    # ------------------------------------------------------------------
    # Indicators / metadata / viewport
    # ------------------------------------------------------------------

    def get_indicators(self, key: str) -> IndicatorEntry | None:
        with self._lock:
            entry = self._indicators.get(key)
            if entry is None:
                return None
            entry.last_access = time.monotonic()
            self._indicators.move_to_end(key)
            return entry

    def put_indicators(
        self,
        key: str,
        fingerprint: str,
        values: dict[str, Any],
    ) -> None:
        with self._lock:
            self._indicators[key] = IndicatorEntry(
                fingerprint=fingerprint,
                values=values,
            )
            self._indicators.move_to_end(key)
            while len(self._indicators) > self.max_series * 4:
                self._indicators.popitem(last=False)

    def get_metadata(self, symbol: str) -> dict[str, Any] | None:
        key = symbol.upper()
        with self._lock:
            value = self._metadata.get(key)
            if value is None:
                return None
            self._metadata.move_to_end(key)
            return dict(value)

    def put_metadata(self, symbol: str, data: dict[str, Any]) -> None:
        key = symbol.upper()
        with self._lock:
            self._metadata[key] = dict(data)
            self._metadata.move_to_end(key)
            while len(self._metadata) > self.max_series:
                self._metadata.popitem(last=False)

    def get_viewport(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._viewports.get(key)
            if value is None:
                return None
            self._viewports.move_to_end(key)
            return dict(value)

    def put_viewport(self, key: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._viewports[key] = dict(data)
            self._viewports.move_to_end(key)
            while len(self._viewports) > self.max_series:
                self._viewports.popitem(last=False)

    # ------------------------------------------------------------------
    # Invalidation / cleanup
    # ------------------------------------------------------------------

    def invalidate(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> int:
        """
        Drop matching series (and related indicator keys).

        Returns number of series entries removed.
        """

        with self._lock:
            if symbol is None and timeframe is None:
                count = len(self._series)
                self._series.clear()
                self._indicators.clear()
                cache_log("CACHE INVALIDATED", scope="all")
                return count

            targets: list[str] = []
            for key in list(self._series.keys()):
                sym, tf = key.split(":", 1)
                if symbol and sym != symbol.upper():
                    continue
                if timeframe and tf != timeframe.upper():
                    continue
                targets.append(key)

            for key in targets:
                self._series.pop(key, None)
                # Drop indicator entries for this series.
                prefix = f"{key}:"
                for ind_key in [
                    k for k in self._indicators if k.startswith(prefix) or k == key
                ]:
                    self._indicators.pop(ind_key, None)

            if targets:
                cache_log(
                    "CACHE INVALIDATED",
                    symbol=symbol or "*",
                    timeframe=timeframe or "*",
                    series=len(targets),
                )
            return len(targets)

    def cleanup_inactive(self) -> int:
        """Remove series not accessed within inactive TTL."""

        now = time.monotonic()
        removed = 0
        with self._lock:
            for key in list(self._series.keys()):
                entry = self._series[key]
                if now - entry.last_access > self.inactive_ttl_seconds:
                    self._series.pop(key, None)
                    removed += 1
            if removed:
                cache_log("INACTIVE CLEANUP", removed=removed)
        return removed

    def stats(self) -> dict[str, Any]:
        with self._lock:
            candle_count = sum(len(e.candles) for e in self._series.values())
            approx_bytes = candle_count * BYTES_PER_CANDLE
            return {
                "series": len(self._series),
                "candles": candle_count,
                "indicators": len(self._indicators),
                "metadata": len(self._metadata),
                "viewports": len(self._viewports),
                "approx_memory_mb": round(approx_bytes / (1024 * 1024), 2),
                "max_memory_mb": round(
                    self.max_memory_bytes / (1024 * 1024), 2
                ),
                "max_candles_per_series": self.max_candles_per_series,
            }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _dedupe_sort(candles: list[CandleTuple]) -> list[CandleTuple]:
        by_time: dict[int, CandleTuple] = {}
        for bar in candles:
            by_time[bar[0]] = bar
        return [by_time[k] for k in sorted(by_time)]

    def _enforce_limits(self) -> None:
        self.cleanup_inactive()

        while len(self._series) > self.max_series:
            key, _ = self._series.popitem(last=False)
            cache_log("RAM EVICT", reason="max_series", key=key)

        candle_count = sum(len(e.candles) for e in self._series.values())
        approx_bytes = candle_count * BYTES_PER_CANDLE
        # Prefer estimated size; fall back to sys.getsizeof sample.
        if approx_bytes <= self.max_memory_bytes:
            return

        while self._series and approx_bytes > self.max_memory_bytes:
            key, entry = self._series.popitem(last=False)
            approx_bytes -= len(entry.candles) * BYTES_PER_CANDLE
            cache_log(
                "RAM EVICT",
                reason="max_memory",
                key=key,
                freed_candles=len(entry.candles),
            )
