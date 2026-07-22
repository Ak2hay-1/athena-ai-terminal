"""
Indicator result cache with incremental-friendly fingerprints.

If no new candle exists for a series, cached indicator values are
returned. When only the newest closed bar changes, consumers can pass
the updated fingerprint so stale results are recomputed once.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any
from typing import Callable

from app.cache.logging_utils import cache_log
from app.cache.ram_cache import RamCache
from app.cache.types import CandleTuple


class IndicatorCache:
    """
    Cache indicator payloads keyed by (symbol, timeframe, indicator set).

    The actual computation callback is injected so this module stays free
    of heavy pandas imports at import time.
    """

    def __init__(self, ram: RamCache, *, enabled: bool = True) -> None:
        self._ram = ram
        self.enabled = enabled
        self._lock = threading.Lock()

    @staticmethod
    def fingerprint(
        candles: list[CandleTuple],
        indicator_ids: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> str:
        if not candles:
            return "empty"
        last = candles[-1]
        payload = {
            "n": len(candles),
            "t": last[0],
            "c": last[4],
            "ids": sorted(indicator_ids or []),
            "params": params or {},
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]

    def get_or_compute(
        self,
        symbol: str,
        timeframe: str,
        candles: list[CandleTuple],
        compute: Callable[[list[CandleTuple]], dict[str, Any]],
        *,
        indicator_ids: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled or not candles:
            return compute(candles)

        fp = self.fingerprint(candles, indicator_ids, params)
        key = f"{symbol.upper()}:{timeframe.upper()}:ind"

        with self._lock:
            entry = self._ram.get_indicators(key)
            if entry is not None and entry.fingerprint == fp:
                cache_log(
                    "INDICATOR CACHE HIT",
                    symbol=symbol,
                    timeframe=timeframe,
                )
                return dict(entry.values)

        cache_log(
            "INDICATOR CACHE MISS",
            symbol=symbol,
            timeframe=timeframe,
        )
        values = compute(candles)
        with self._lock:
            self._ram.put_indicators(key, fp, values)
        return values

    def invalidate(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> None:
        # Indicator entries live inside RamCache; series invalidation
        # already clears matching indicator keys.
        self._ram.invalidate(symbol, timeframe)
