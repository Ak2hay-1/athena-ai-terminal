"""
CacheManager – single entry point for Athena market caches.

Responsibilities:
- Layer 1 RAM cache (LRU candle series, indicators, metadata)
- Layer 2 local database (PostgreSQL market_candles)
- Layer 3 MT5 gap-only synchronization
- Cache validation / invalidation
- Background preload scheduling
- Performance metrics

Safety: never caches live account state (positions, orders, margin,
balance, equity). Live bid/ask for trading always come from MT5 / the
live tick path — historical candles never include the forming bar as
immutable history.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

from app.cache.ai_context_cache import AiContextCache
from app.cache.indicator_cache import IndicatorCache
from app.cache.logging_utils import cache_log
from app.cache.metrics import MetricsCollector
from app.cache.preloader import BackgroundPreloader
from app.cache.ram_cache import RamCache
from app.cache.types import CandleDict
from app.cache.types import CandleTuple
from app.cache.types import model_to_tuple
from app.cache.types import tuple_to_dict


class CacheManager:
    """Facade over the three-layer market cache."""

    def __init__(self) -> None:
        from app.core.settings import settings

        self._settings = settings
        self.metrics = MetricsCollector()

        self.ram = RamCache(
            max_candles_per_series=int(
                getattr(settings, "CACHE_MAX_RAM_CANDLES", 5000)
            ),
            max_memory_mb=float(
                getattr(settings, "CACHE_MAX_RAM_MB", 256.0)
            ),
            inactive_ttl_seconds=float(
                getattr(settings, "CACHE_INACTIVE_TTL_SECONDS", 900.0)
            ),
            max_series=int(getattr(settings, "CACHE_MAX_SERIES", 128)),
        )

        self.indicators = IndicatorCache(
            self.ram,
            enabled=bool(
                getattr(settings, "CACHE_INDICATOR_ENABLED", True)
            ),
        )

        self.ai = AiContextCache(
            ttl_seconds=float(
                getattr(settings, "CACHE_AI_TTL_SECONDS", 45.0)
            ),
        )

        related = list(
            getattr(
                settings,
                "CACHE_PRELOAD_TIMEFRAMES",
                ["M1", "M15", "H1", "H4"],
            )
        )
        self.preloader = BackgroundPreloader(
            warm_fn=self._warm_series,
            enabled=bool(getattr(settings, "CACHE_PRELOAD_ENABLED", True)),
            workers=int(getattr(settings, "CACHE_PRELOAD_WORKERS", 2)),
            default_limit=int(
                getattr(settings, "CACHE_PRELOAD_LIMIT", 500)
            ),
            related_timeframes=related,
        )

        self._lock = threading.RLock()
        self._started = False
        self._cleanup_thread: threading.Thread | None = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._stop.clear()
        self.preloader.start()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="athena-cache-cleanup",
            daemon=True,
        )
        self._cleanup_thread.start()
        cache_log("CACHE MANAGER STARTED")

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        self._stop.set()
        self.preloader.stop()
        cache_log("CACHE MANAGER STOPPED")

    # ------------------------------------------------------------------
    # Primary read path: RAM → DB → (optional) MT5 sync
    # ------------------------------------------------------------------

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        *,
        before: datetime | None = None,
        sync_if_stale: bool = True,
        trigger_preload: bool = True,
    ) -> list[CandleDict]:
        """
        Return the latest ``limit`` completed candles.

        Flow:
            1. RAM HIT  → return immediately
            2. DATABASE → hydrate RAM, return
            3. If empty / stale and sync enabled → MT5 gap sync, retry DB
        """

        symbol = symbol.upper()
        timeframe = timeframe.upper()
        limit = max(1, min(int(limit), 10_000))
        before_epoch = (
            int(before.timestamp())
            if before is not None
            else None
        )

        # ---- Layer 1: RAM ----
        if before_epoch is None:
            cached = self.ram.get_candles(
                symbol, timeframe, limit=limit
            )
            # Hit when RAM has a full page, or any bars and we will not
            # block the UI waiting on a deeper DB fill for short series.
            if cached is not None and len(cached) >= limit:
                self.metrics.incr("ram_hits")
                cache_log(
                    "RAM HIT",
                    symbol=symbol,
                    timeframe=timeframe,
                    count=len(cached),
                )
                if trigger_preload:
                    self.preloader.on_chart_open(
                        symbol, timeframe, limit=limit
                    )
                return [
                    tuple_to_dict(c, symbol=symbol, timeframe=timeframe)
                    for c in cached
                ]
        else:
            # Pagination: serve from RAM only when the series reaches
            # older than the cursor (otherwise older history is in DB).
            full = self.ram.get_candles(symbol, timeframe)
            if full and full[0][0] < before_epoch:
                cached = [c for c in full if c[0] < before_epoch][-limit:]
                if cached:
                    self.metrics.incr("ram_hits")
                    cache_log(
                        "RAM HIT",
                        symbol=symbol,
                        timeframe=timeframe,
                        count=len(cached),
                        before=before_epoch,
                    )
                    return [
                        tuple_to_dict(c, symbol=symbol, timeframe=timeframe)
                        for c in cached
                    ]

        self.metrics.incr("ram_misses")
        cache_log(
            "RAM MISS",
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        # ---- Layer 2: Database ----
        rows = self._load_from_db(
            symbol, timeframe, limit, before=before
        )
        if rows:
            self.metrics.incr("db_hits")
            cache_log(
                "DATABASE HIT",
                symbol=symbol,
                timeframe=timeframe,
                count=len(rows),
            )
            if before is None:
                # Hydrate RAM with a deeper window for future TF switches.
                hydrate_limit = max(
                    limit,
                    int(
                        getattr(
                            self._settings,
                            "CACHE_MAX_RAM_CANDLES",
                            5000,
                        )
                    ),
                )
                deep = (
                    rows
                    if len(rows) >= hydrate_limit
                    else self._load_from_db(
                        symbol, timeframe, hydrate_limit
                    )
                )
                self.ram.put_candles(
                    symbol,
                    timeframe,
                    [model_to_tuple(r) for r in deep],
                    replace=True,
                )
            if trigger_preload and before is None:
                self.preloader.on_chart_open(
                    symbol, timeframe, limit=limit
                )
            return [
                tuple_to_dict(
                    model_to_tuple(r),
                    symbol=symbol,
                    timeframe=timeframe,
                )
                for r in rows
            ]

        self.metrics.incr("db_misses")
        cache_log(
            "DATABASE MISS",
            symbol=symbol,
            timeframe=timeframe,
        )

        # ---- Layer 3: MT5 gap / initial sync ----
        if sync_if_stale and before is None:
            inserted = self.sync_symbol(symbol, timeframe)
            if inserted:
                rows = self._load_from_db(symbol, timeframe, limit)
                if rows:
                    self.ram.put_candles(
                        symbol,
                        timeframe,
                        [model_to_tuple(r) for r in rows],
                        replace=True,
                    )
                    if trigger_preload:
                        self.preloader.on_chart_open(
                            symbol, timeframe, limit=limit
                        )
                    return [
                        tuple_to_dict(
                            model_to_tuple(r),
                            symbol=symbol,
                            timeframe=timeframe,
                        )
                        for r in rows
                    ]

        return []

    def get_latest_candle(
        self,
        symbol: str,
        timeframe: str,
    ) -> CandleDict | None:
        candles = self.get_candles(
            symbol,
            timeframe,
            limit=1,
            sync_if_stale=False,
            trigger_preload=False,
        )
        return candles[-1] if candles else None

    # ------------------------------------------------------------------
    # Writes from the live pipeline (completed candles only)
    # ------------------------------------------------------------------

    def on_candle_closed(
        self,
        symbol: str,
        timeframe: str,
        candle: Any,
    ) -> None:
        """
        Promote a completed candle into RAM (+ invalidate AI context).

        The persistence writer still owns durable DB writes. Forming
        candles must never call this.
        """

        symbol = symbol.upper()
        timeframe = timeframe.upper()
        bar = model_to_tuple(candle)
        self.ram.append_closed_candle(symbol, timeframe, bar)
        self.ai.invalidate_on_candle(symbol, timeframe, bar[0])
        # Indicator fingerprint will miss on next read automatically.

    def put_series(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Any],
    ) -> None:
        """Replace RAM series from an external hydrate (e.g. sync)."""

        bars = [model_to_tuple(c) for c in candles]
        self.ram.put_candles(symbol, timeframe, bars, replace=True)

    # ------------------------------------------------------------------
    # Indicators
    # ------------------------------------------------------------------

    def get_indicators(
        self,
        symbol: str,
        timeframe: str,
        candles: list[CandleTuple] | None = None,
        compute: Any | None = None,
        *,
        indicator_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if candles is None:
            cached = self.ram.get_candles(symbol, timeframe, limit=500)
            candles = cached or []

        if compute is None:
            # Return last known Redis/RAM indicator snapshot if any.
            from app.marketdata.live_cache import live_market_cache

            snap = live_market_cache.get_indicators(symbol, timeframe)
            return dict(snap or {})

        result = self.indicators.get_or_compute(
            symbol,
            timeframe,
            candles,
            compute,
            indicator_ids=indicator_ids,
        )
        # Metrics: indicator cache logs hit/miss; count via fingerprint path.
        return result

    # ------------------------------------------------------------------
    # AI context
    # ------------------------------------------------------------------

    def get_ai_context(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        hit = self.ai.get(symbol, timeframe)
        if hit is not None:
            self.metrics.incr("ai_hits")
            cache_log("AI CACHE HIT", symbol=symbol, timeframe=timeframe)
            return hit
        self.metrics.incr("ai_misses")
        return None

    def set_ai_context(
        self,
        symbol: str,
        timeframe: str,
        payload: dict[str, Any],
        *,
        candle_epoch: int | None = None,
    ) -> None:
        self.ai.set(
            symbol,
            timeframe,
            payload,
            candle_epoch=candle_epoch,
        )

    # ------------------------------------------------------------------
    # Metadata / viewport
    # ------------------------------------------------------------------

    def get_symbol_metadata(self, symbol: str) -> dict[str, Any] | None:
        return self.ram.get_metadata(symbol)

    def set_symbol_metadata(
        self, symbol: str, data: dict[str, Any]
    ) -> None:
        self.ram.put_metadata(symbol, data)

    def get_viewport(self, key: str) -> dict[str, Any] | None:
        return self.ram.get_viewport(key)

    def set_viewport(self, key: str, data: dict[str, Any]) -> None:
        self.ram.put_viewport(key, data)

    # ------------------------------------------------------------------
    # Sync / invalidation
    # ------------------------------------------------------------------

    def sync_symbol(self, symbol: str, timeframe: str) -> int:
        """Layer 3: download only missing completed candles from MT5."""

        cache_log("SYNC START", symbol=symbol, timeframe=timeframe)
        started = time.perf_counter()
        try:
            from app.marketdata.sync import history_synchronizer

            inserted = history_synchronizer.sync_symbol(
                symbol.upper(), timeframe.upper()
            )
        except Exception:
            from app.core.logger import get_logger

            get_logger("athena.cache").exception(
                "MT5 sync failed for %s %s", symbol, timeframe
            )
            inserted = 0

        self.metrics.incr("sync_runs")
        self.metrics.incr("sync_candles", inserted)
        cache_log(
            "SYNC COMPLETE",
            symbol=symbol,
            timeframe=timeframe,
            inserted=inserted,
            ms=round((time.perf_counter() - started) * 1000, 1),
        )

        if inserted:
            # Refresh RAM from DB so consumers never see stale history.
            self.invalidate(symbol, timeframe, reason="sync")
            rows = self._load_from_db(
                symbol,
                timeframe,
                int(
                    getattr(
                        self._settings, "CACHE_MAX_RAM_CANDLES", 5000
                    )
                ),
            )
            if rows:
                self.ram.put_candles(
                    symbol,
                    timeframe,
                    [model_to_tuple(r) for r in rows],
                    replace=True,
                )
        return inserted

    def sync_on_reconnect(
        self,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
    ) -> int:
        """
        After MT5 reconnect: compare latest cached vs MT5 and fill gaps.
        """

        cache_log("SYNC START", reason="reconnect")
        try:
            from app.marketdata.sync import history_synchronizer

            inserted = history_synchronizer.sync_gaps_only(
                symbols=symbols,
                timeframes=timeframes,
            )
        except Exception:
            from app.core.logger import get_logger

            get_logger("athena.cache").exception(
                "Reconnect gap sync failed"
            )
            inserted = 0

        self.metrics.incr("sync_runs")
        self.metrics.incr("sync_candles", inserted)
        cache_log("SYNC COMPLETE", reason="reconnect", inserted=inserted)

        if inserted:
            self.invalidate(reason="reconnect")
        return inserted

    def invalidate(
        self,
        symbol: str | None = None,
        timeframe: str | None = None,
        *,
        reason: str = "manual",
    ) -> None:
        removed = self.ram.invalidate(symbol, timeframe)
        self.ai.invalidate(symbol, timeframe, reason=reason)
        self.metrics.incr("invalidations")
        cache_log(
            "CACHE INVALIDATED",
            reason=reason,
            symbol=symbol or "*",
            timeframe=timeframe or "*",
            series=removed,
        )

    def on_manual_refresh(
        self, symbol: str, timeframe: str
    ) -> list[CandleDict]:
        """Manual refresh: invalidate, sync gaps, return fresh series."""

        self.invalidate(symbol, timeframe, reason="manual_refresh")
        self.sync_symbol(symbol, timeframe)
        return self.get_candles(
            symbol,
            timeframe,
            limit=int(
                getattr(self._settings, "CACHE_PRELOAD_LIMIT", 500)
            ),
            sync_if_stale=False,
            trigger_preload=True,
        )

    def set_watchlist(self, symbols: list[str]) -> None:
        self.preloader.set_watchlist(symbols)

    # ------------------------------------------------------------------
    # Metrics / health
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        return {
            "started": self._started,
            "ram": self.ram.stats(),
            "ai": self.ai.stats(),
            "metrics": self.metrics.snapshot(),
            "preload_enabled": self.preloader.enabled,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _warm_series(self, symbol: str, timeframe: str, limit: int) -> None:
        """Preloader callback — populate RAM without MT5 unless empty."""

        self.metrics.incr("preloads_started")
        existing = self.ram.get_candles(symbol, timeframe, limit=1)
        if existing:
            self.metrics.incr("preloads_completed")
            return

        rows = self._load_from_db(symbol, timeframe, limit)
        if rows:
            self.ram.put_candles(
                symbol,
                timeframe,
                [model_to_tuple(r) for r in rows],
                replace=True,
            )
        else:
            # Only hit MT5 when local DB is empty for this series.
            self.sync_symbol(symbol, timeframe)
        self.metrics.incr("preloads_completed")

    def _load_from_db(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        before: datetime | None = None,
    ) -> list[Any]:
        try:
            from app.database.database import SessionLocal
            from app.repositories.market_repository import MarketRepository

            db = SessionLocal()
            try:
                repository = MarketRepository(db)
                return repository.get_latest_candles(
                    symbol.upper(),
                    timeframe.upper(),
                    limit=limit,
                    before=before,
                )
            finally:
                db.close()
        except Exception:
            from app.core.logger import get_logger

            get_logger("athena.cache").exception(
                "Database candle load failed for %s %s",
                symbol,
                timeframe,
            )
            return []

    def _cleanup_loop(self) -> None:
        while not self._stop.wait(60.0):
            try:
                self.ram.cleanup_inactive()
            except Exception:
                pass


cache_manager = CacheManager()
