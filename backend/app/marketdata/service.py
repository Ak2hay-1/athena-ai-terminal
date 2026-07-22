"""
Market Data Service (orchestrator).

Wires the tick-to-candle pipeline together:

    TickCollector -> CandleEngine
        closed candles -> PersistenceWriter -> PostgreSQL
                        -> IndicatorUpdater -> indicator_values + Redis
                        -> WebSocket broadcast -> React chart
                        -> Analysis dispatcher -> Athena AI
        forming candle -> Redis live cache + throttled WS broadcast
        ticks          -> Redis live cache + throttled WS broadcast

Startup: history loads from the local database; only candles missing
since the newest stored candle are downloaded from MT5 (in the
background, so startup completes within seconds regardless of database
size). Reconnects trigger the same gap-only sync.
"""

from __future__ import annotations

import queue
import threading
import time as time_module

from app.core.logger import get_logger
from app.core.settings import settings
from app.marketdata.collector import TickCollector
from app.marketdata.engine import Candle
from app.marketdata.engine import CandleEngine
from app.marketdata.engine import EngineCallbacks
from app.marketdata.indicator_updater import indicator_updater
from app.marketdata.live_cache import live_market_cache
from app.marketdata.persistence import PersistenceWriter
from app.marketdata.sync import history_synchronizer
from app.marketdata.ticks import Tick
from app.marketdata.timeframes import epoch_to_datetime

logger = get_logger("athena.marketdata.service")


class MarketDataService:
    """Owns the lifecycle of the market data engine."""

    def __init__(self) -> None:
        self.engine = CandleEngine(
            timeframes=list(settings.MARKET_TIMEFRAMES),
            callbacks=EngineCallbacks(
                on_tick=self._on_tick,
                on_candle_forming=self._on_candle_forming,
                on_candle_closed=self._on_candle_closed,
            ),
        )
        self.writer = PersistenceWriter(
            flush_interval_s=float(settings.MARKET_WRITE_FLUSH_SECONDS),
            store_ticks=bool(settings.MARKET_STORE_TICKS),
        )
        self.collector = TickCollector(
            engine=self.engine,
            on_reconnected=self._on_mt5_reconnected,
        )

        self._started = False
        self._sync_thread: threading.Thread | None = None

        # Broadcast throttles (per key -> last emit monotonic seconds).
        self._last_tick_emit: dict[str, float] = {}
        self._last_forming_emit: dict[str, float] = {}
        self._throttle_s = max(50, int(settings.TICK_POLL_MS)) / 1000.0

        # Analysis worker: one deduped queue so candle-close analysis
        # can never back up the tick path.
        self._analysis_queue: queue.Queue = queue.Queue(maxsize=200)
        self._analysis_pending: set[tuple[str, str]] = set()
        self._analysis_lock = threading.Lock()
        self._analysis_thread: threading.Thread | None = None
        self._stop = threading.Event()

        # Gap healer: wakes when a partial candle closes or MT5
        # reconnects, then fills missing completed candles from MT5.
        self._heal_event = threading.Event()
        self._heal_thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._stop.clear()

        self.writer.start()
        self._seed_engine_from_db()

        # History sync runs in the background so startup stays fast.
        self._sync_thread = threading.Thread(
            target=self._startup_sync,
            name="athena-history-sync",
            daemon=True,
        )
        self._sync_thread.start()

        self._analysis_thread = threading.Thread(
            target=self._analysis_worker,
            name="athena-candle-analysis",
            daemon=True,
        )
        self._analysis_thread.start()

        self._heal_thread = threading.Thread(
            target=self._heal_worker,
            name="athena-gap-healer",
            daemon=True,
        )
        self._heal_thread.start()

        self.collector.start()
        logger.info("Market data engine started.")

    def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        self._stop.set()

        self.collector.stop()

        # Persist forming candles' final state? No — forming candles are
        # mutable and only completed candles are stored. Time-based
        # closing on next startup + gap sync rebuilds anything missed.
        self.writer.stop()

        thread = self._analysis_thread
        if thread is not None:
            thread.join(timeout=5.0)
            self._analysis_thread = None

        logger.info("Market data engine stopped.")

    def status(self) -> dict:
        return {
            "started": self._started,
            "engine": self.engine.metrics(),
            "collector": self.collector.metrics(),
            "writer": self.writer.metrics(),
        }

    # ------------------------------------------------------------------
    # Startup helpers
    # ------------------------------------------------------------------

    def _seed_engine_from_db(self) -> None:
        """
        Seed each builder with the newest stored candle so late ticks
        cannot regenerate already-persisted buckets.
        """

        try:
            from app.database.database import SessionLocal
            from app.marketdata.timeframes import bucket_start_epoch
            from app.marketdata.timeframes import timeframe_seconds
            from app.mt5.sdk import mt5
            from app.repositories.market_repository import MarketRepository

            # Repair historical rows written with local TZ labeled as UTC
            # before seeding — a future floor discards every live tick.
            self._repair_candle_time_skew()

            db = SessionLocal()
            try:
                repository = MarketRepository(db)
                broker_now_by_symbol: dict[str, int] = {}
                for symbol in settings.MARKET_SYMBOLS:
                    for timeframe in settings.MARKET_TIMEFRAMES:
                        newest = repository.get_latest(
                            symbol.upper(), timeframe.upper()
                        )
                        if newest is None:
                            continue
                        floor = int(newest.time.timestamp())
                        sym = symbol.upper()
                        if sym not in broker_now_by_symbol:
                            tick = mt5.symbol_info_tick(sym)
                            broker_now_by_symbol[sym] = (
                                int(getattr(tick, "time", 0) or 0)
                                if tick is not None
                                else 0
                            )
                        broker_now = broker_now_by_symbol[sym]
                        if broker_now:
                            current_bucket = bucket_start_epoch(
                                broker_now, timeframe
                            )
                            if floor >= current_bucket:
                                duration = timeframe_seconds(timeframe)
                                floor = max(0, current_bucket - duration)
                                logger.warning(
                                    "Clamped engine seed for %s %s "
                                    "(DB floor was at/after live bucket)",
                                    sym,
                                    timeframe.upper(),
                                )
                        self.engine.seed_last_completed(
                            symbol,
                            timeframe,
                            floor,
                        )
            finally:
                db.close()
        except Exception:
            logger.exception("Engine seed from database failed")

    def _repair_candle_time_skew(self) -> None:
        """
        If market_candles times were stored as local wall-clock labeled
        UTC (common Windows IST bug), shift them back by the detected
        offset so the live engine can close candles again.
        """

        try:
            from datetime import datetime as _dt
            from datetime import timedelta

            from sqlalchemy import text

            from app.database.database import SessionLocal
            from app.mt5.client import mt5_client
            from app.mt5.sdk import mt5

            if not mt5_client.initialize():
                return

            local_offset = int(
                (_dt.now().astimezone().utcoffset() or timedelta()).total_seconds()
            )
            if local_offset == 0:
                return

            sample_symbol = str(settings.MARKET_SYMBOLS[0]).upper()
            tick = mt5.symbol_info_tick(sample_symbol)
            rates = mt5.copy_rates_from_pos(
                sample_symbol, mt5.TIMEFRAME_M1, 0, 3
            )
            if tick is None or rates is None or len(rates) < 2:
                return

            # Last completed M1 bar (exclude forming).
            mt5_completed = int(rates[-2]["time"])
            db = SessionLocal()
            try:
                row = db.execute(
                    text(
                        "SELECT EXTRACT(EPOCH FROM time)::bigint AS epoch "
                        "FROM market_candles "
                        "WHERE symbol = :symbol AND timeframe = 'M1' "
                        "ORDER BY time DESC LIMIT 1"
                    ),
                    {"symbol": sample_symbol},
                ).mappings().first()
                if row is None:
                    return
                db_epoch = int(row["epoch"])
                skew = db_epoch - mt5_completed
                if abs(skew - local_offset) > 120:
                    return

                # Rows stamped in the future vs broker clock are the ones
                # blocking the live engine. Drop them; gap heal refills.
                broker_now = int(getattr(tick, "time", 0) or mt5_completed)
                result = db.execute(
                    text(
                        "DELETE FROM market_candles "
                        "WHERE EXTRACT(EPOCH FROM time) > :broker_now"
                    ),
                    {"broker_now": broker_now},
                )
                db.commit()
                logger.warning(
                    "Repaired market_candles timezone skew: "
                    "deleted %s future-stamped rows "
                    "(skew≈%ss local_offset=%ss); gap heal will refill",
                    result.rowcount,
                    int(skew),
                    local_offset,
                )
            finally:
                db.close()
        except Exception:
            logger.exception("Candle time skew repair failed")

    def _startup_sync(self) -> None:
        """Initial deep sync (first run) or gap-only fill (restarts)."""

        try:
            history_synchronizer.sync_all()
        except Exception:
            logger.exception("Startup history sync failed")

    def _on_mt5_reconnected(self) -> None:
        """After downtime: download only the missing completed candles."""

        try:
            from app.cache import cache_manager
            from app.core.settings import settings as _settings

            if _settings.CACHE_ENABLED:
                cache_manager.invalidate(reason="mt5_reconnect")
        except Exception:
            logger.exception("Cache invalidation on reconnect failed")

        self._heal_event.set()

    def _heal_worker(self) -> None:
        """
        Serialized gap healing. Each missed period is downloaded from
        MT5 as discrete completed candles — never merged into one
        oversized candle.
        """

        while not self._stop.is_set():
            if not self._heal_event.wait(timeout=1.0):
                continue
            self._heal_event.clear()
            try:
                history_synchronizer.sync_gaps_only()
                try:
                    from app.cache import cache_manager
                    from app.core.settings import settings as _settings

                    if _settings.CACHE_ENABLED:
                        # Drop stale RAM series so the next read hydrates
                        # from the freshly synced database.
                        cache_manager.invalidate(reason="gap_heal")
                except Exception:
                    logger.exception(
                        "Cache invalidation after gap heal failed"
                    )
            except Exception:
                logger.exception("Gap healing failed")

    # ------------------------------------------------------------------
    # Engine callbacks (collector thread)
    # ------------------------------------------------------------------

    def _on_tick(self, tick: Tick) -> None:
        self.writer.enqueue_tick(tick)

        now = time_module.monotonic()
        last = self._last_tick_emit.get(tick.symbol, 0.0)
        if now - last < self._throttle_s:
            return
        self._last_tick_emit[tick.symbol] = now

        time_iso = epoch_to_datetime(tick.epoch_seconds).isoformat()

        live_market_cache.set_tick(
            {
                "symbol": tick.symbol,
                "time": time_iso,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "mid": tick.mid,
                "spread": tick.spread,
            }
        )
        live_market_cache.set_market_state(
            tick.symbol,
            {
                "symbol": tick.symbol,
                "spread": tick.spread,
                "status": "open",
                "last_tick_time": time_iso,
            },
        )

        try:
            from app.services.websocket_broadcast import broadcast_tick_update

            broadcast_tick_update(
                symbol=tick.symbol,
                bid=tick.bid,
                ask=tick.ask,
                mid=tick.mid,
                time=time_iso,
            )
        except Exception:
            logger.exception("Tick broadcast failed for %s", tick.symbol)

    def _on_candle_forming(self, candle: Candle) -> None:
        key = f"{candle.symbol}:{candle.timeframe}"
        now = time_module.monotonic()
        last = self._last_forming_emit.get(key, 0.0)
        if now - last < self._throttle_s:
            return
        self._last_forming_emit[key] = now

        live_market_cache.set_current_candle(candle.to_payload())

    def _on_candle_closed(self, candle: Candle) -> None:
        # 1. Save candle (immutable, batched but reliable). Candles that
        #    may have missed ticks (startup / reconnect mid-bucket) are
        #    not persisted from ticks; the true completed bar is pulled
        #    from MT5 by the gap healer instead.
        if candle.partial:
            self._heal_event.set()
        else:
            self.writer.enqueue_candle(candle)

        # 2. Update indicators for the newly completed candle only.
        values = None
        if not candle.partial:
            values = indicator_updater.on_candle_closed(candle)

        # 2b. Promote completed candle into CacheManager RAM series
        #     (never stores forming / partial bars as history).
        if not candle.partial:
            try:
                from app.cache import cache_manager
                from app.core.settings import settings as _settings

                if _settings.CACHE_ENABLED:
                    cache_manager.on_candle_closed(
                        candle.symbol,
                        candle.timeframe,
                        {
                            "time": candle.bucket_start,
                            "open": candle.open,
                            "high": candle.high,
                            "low": candle.low,
                            "close": candle.close,
                            "tick_volume": candle.tick_volume,
                            "spread": 0,
                            "real_volume": 0,
                        },
                    )
            except Exception:
                logger.exception("CacheManager candle update failed")

        # 3. Update Redis: closed candle becomes latest completed state.
        live_market_cache.set_current_candle(candle.to_payload())

        # 4. Broadcast to chart subscribers (single-candle update; the
        #    frontend merges by bucket without reloading history).
        try:
            from app.services.websocket_broadcast import (
                broadcast_candle_update,
            )

            broadcast_candle_update(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                inserted=1,
                candle=candle.to_payload(),
            )
        except Exception:
            logger.exception(
                "Candle broadcast failed for %s %s",
                candle.symbol,
                candle.timeframe,
            )

        # 5. Notify AI: event bus + queued local analysis.
        try:
            from app.events.async_bridge import schedule_publish
            from app.events.types import EventType

            schedule_publish(
                EventType.MARKET_UPDATED,
                {
                    "symbol": candle.symbol,
                    "timeframe": candle.timeframe,
                    "time": epoch_to_datetime(
                        candle.bucket_start
                    ).isoformat(),
                    "close": candle.close,
                    "indicators": values or {},
                },
                source="market_data_engine",
            )
        except Exception:
            logger.exception("MarketUpdated publish failed")

        if settings.MARKET_ANALYZE_ON_CLOSE:
            self._enqueue_analysis(candle.symbol, candle.timeframe)

    # ------------------------------------------------------------------
    # Analysis worker
    # ------------------------------------------------------------------

    def _enqueue_analysis(self, symbol: str, timeframe: str) -> None:
        key = (symbol, timeframe)
        with self._analysis_lock:
            if key in self._analysis_pending:
                return
            self._analysis_pending.add(key)
        try:
            self._analysis_queue.put_nowait(key)
        except queue.Full:
            with self._analysis_lock:
                self._analysis_pending.discard(key)

    def _analysis_worker(self) -> None:
        while not self._stop.is_set():
            try:
                key = self._analysis_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            symbol, timeframe = key
            with self._analysis_lock:
                self._analysis_pending.discard(key)

            try:
                self._run_analysis(symbol, timeframe)
            except Exception:
                logger.exception(
                    "Candle-close analysis failed for %s %s",
                    symbol,
                    timeframe,
                )

    def _run_analysis(self, symbol: str, timeframe: str) -> None:
        """
        AI analysis uses Athena's local data only (DB candles + Redis
        state) — it never requests history from MT5.
        """

        from app.database.database import SessionLocal
        from app.services.market_service import MarketService
        from app.services.websocket_broadcast import broadcast_candle_update

        db = SessionLocal()
        try:
            service = MarketService(db)
            recommendation = service.analyze_latest(
                symbol=symbol,
                timeframe=timeframe,
                explain_with_ai=False,
            )
            if recommendation is not None:
                broadcast_candle_update(
                    symbol=symbol,
                    timeframe=timeframe,
                    inserted=0,
                    recommendation=recommendation,
                )
                self._cache_ai_context(symbol, timeframe, recommendation)
        finally:
            db.close()

    @staticmethod
    def _cache_ai_context(symbol: str, timeframe: str, recommendation) -> None:
        try:
            signal = recommendation.signal
            if hasattr(signal, "value"):
                signal = signal.value
            context = {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": str(signal),
                "confidence": float(recommendation.confidence or 0),
                "entry": getattr(recommendation, "entry", None),
                "stop_loss": getattr(recommendation, "stop_loss", None),
                "take_profit": getattr(
                    recommendation, "take_profit", None
                ),
                "trend": str(getattr(recommendation, "trend", "") or ""),
            }
            live_market_cache.set_ai_context(symbol, timeframe, context)
            try:
                from app.cache import cache_manager
                from app.core.settings import settings as _settings

                if _settings.CACHE_ENABLED:
                    cache_manager.set_ai_context(
                        symbol, timeframe, context
                    )
            except Exception:
                pass
        except Exception:
            logger.exception(
                "AI context cache failed for %s %s", symbol, timeframe
            )


market_data_service = MarketDataService()
