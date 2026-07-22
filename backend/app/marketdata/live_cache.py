"""
Live Market Cache.

Redis-backed cache of the current market state:

    athena:tick:{symbol}                 latest normalized tick
    athena:candle:{symbol}:{timeframe}   current (forming) candle
    athena:indicators:{symbol}:{tf}      latest indicator values
    athena:market:{symbol}               spread / session / status
    athena:ai:{symbol}:{timeframe}       latest AI context summary

Athena AI and API consumers read live state from here instead of
querying MT5 directly. Falls back to an in-process cache when Redis is
unavailable (soft-fail, automatic recovery on reconnect).
"""

from __future__ import annotations

import json
import threading
import time as time_module
from typing import Any

from app.core.logger import get_logger

logger = get_logger("athena.marketdata.live_cache")

_TTL_SECONDS = 24 * 3600


class LiveMarketCache:
    """Current market state store (Redis with in-memory fallback)."""

    def __init__(self) -> None:
        self._memory: dict[str, str] = {}
        self._lock = threading.Lock()
        self._redis_down_logged = False

    # ------------------------------------------------------------------
    # Writers (called from engine/collector threads)
    # ------------------------------------------------------------------

    def set_tick(self, payload: dict[str, Any]) -> None:
        symbol = str(payload.get("symbol", "")).upper()
        if not symbol:
            return
        self._set(f"athena:tick:{symbol}", payload)

    def set_current_candle(self, payload: dict[str, Any]) -> None:
        symbol = str(payload.get("symbol", "")).upper()
        timeframe = str(payload.get("timeframe", "")).upper()
        if not symbol or not timeframe:
            return
        self._set(f"athena:candle:{symbol}:{timeframe}", payload)

    def set_indicators(
        self,
        symbol: str,
        timeframe: str,
        values: dict[str, Any],
    ) -> None:
        self._set(
            f"athena:indicators:{symbol.upper()}:{timeframe.upper()}",
            values,
        )

    def set_market_state(self, symbol: str, state: dict[str, Any]) -> None:
        self._set(f"athena:market:{symbol.upper()}", state)

    def set_ai_context(
        self,
        symbol: str,
        timeframe: str,
        context: dict[str, Any],
    ) -> None:
        self._set(
            f"athena:ai:{symbol.upper()}:{timeframe.upper()}",
            context,
        )

    # ------------------------------------------------------------------
    # Readers
    # ------------------------------------------------------------------

    def get_tick(self, symbol: str) -> dict[str, Any] | None:
        return self._get(f"athena:tick:{symbol.upper()}")

    def get_current_candle(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        return self._get(
            f"athena:candle:{symbol.upper()}:{timeframe.upper()}"
        )

    def get_indicators(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        return self._get(
            f"athena:indicators:{symbol.upper()}:{timeframe.upper()}"
        )

    def get_market_state(self, symbol: str) -> dict[str, Any] | None:
        return self._get(f"athena:market:{symbol.upper()}")

    def get_ai_context(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        return self._get(f"athena:ai:{symbol.upper()}:{timeframe.upper()}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _set(self, key: str, value: dict[str, Any]) -> None:
        try:
            encoded = json.dumps(
                {**value, "_cached_at": time_module.time()},
                default=str,
            )
        except (TypeError, ValueError):
            logger.warning("Unserializable live-cache payload for %s", key)
            return

        with self._lock:
            self._memory[key] = encoded

        client = self._redis()
        if client is None:
            return
        try:
            client.set(key, encoded, ex=_TTL_SECONDS)
            self._redis_down_logged = False
        except Exception:
            self._on_redis_error()

    def _get(self, key: str) -> dict[str, Any] | None:
        client = self._redis()
        if client is not None:
            try:
                raw = client.get(key)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                self._on_redis_error()

        with self._lock:
            raw = self._memory.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _redis():
        from app.ai.cache.redis_client import get_redis

        return get_redis()

    def _on_redis_error(self) -> None:
        from app.ai.cache.redis_client import invalidate_redis_client

        invalidate_redis_client()
        if not self._redis_down_logged:
            self._redis_down_logged = True
            logger.warning(
                "Redis unavailable for live market cache; "
                "using in-memory fallback"
            )


live_market_cache = LiveMarketCache()
