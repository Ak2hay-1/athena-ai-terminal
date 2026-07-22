"""
History Synchronizer.

Keeps the local historical database complete using MT5 only for:
- the one-time initial history download, and
- filling gaps after downtime / reconnects.

After the initial synchronization Athena loads history exclusively
from its own database; startup only downloads candles newer than the
latest stored candle. Missing periods become proper discrete candles —
never a single merged oversized candle.
"""

from __future__ import annotations

import threading
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.core.logger import get_logger
from app.core.settings import settings
from app.marketdata.timeframes import bucket_start_epoch
from app.marketdata.timeframes import epoch_to_datetime
from app.marketdata.timeframes import timeframe_seconds
from app.marketdata.timeframes import to_utc
from app.mt5.client import mt5_client
from app.mt5.constants import timeframe_to_mt5
from app.mt5.sdk import mt5

logger = get_logger("athena.marketdata.sync")


class HistorySynchronizer:
    """
    Initial deep sync + incremental gap fill for market candles.

    Thread-safe: a global lock prevents overlapping sync passes (e.g.
    startup sync racing a reconnect-triggered sync).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def sync_symbol(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        """
        Ensure local history is complete for one symbol/timeframe.

        - Empty or shallow database  -> initial deep download.
        - Otherwise                  -> download only missing completed
                                        candles since the newest stored
                                        candle.

        Returns the number of candles inserted.
        """

        symbol = symbol.upper()
        timeframe = timeframe.upper()

        from app.database.database import SessionLocal
        from app.repositories.market_repository import MarketRepository

        db = SessionLocal()
        try:
            repository = MarketRepository(db)
            stats = repository.get_statistics(symbol, timeframe)
            count = int(stats.get("candle_count") or 0)
            newest = stats.get("last_candle")

            threshold = max(
                0, int(settings.MARKET_STARTUP_BACKFILL_THRESHOLD)
            )

            if count < threshold or newest is None:
                inserted = self._initial_sync(db, symbol, timeframe)
            else:
                inserted = self._gap_sync(
                    db,
                    symbol,
                    timeframe,
                    to_utc(newest),
                )

            return inserted
        finally:
            db.close()

    def sync_all(
        self,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
    ) -> int:
        """Synchronize every configured symbol/timeframe pair."""

        if not mt5_client.initialize():
            logger.warning("History sync skipped: MT5 unavailable.")
            return 0

        if not self._lock.acquire(blocking=False):
            logger.info("History sync already running; skipping.")
            return 0

        try:
            total = 0
            for timeframe in timeframes or settings.MARKET_TIMEFRAMES:
                for symbol in symbols or settings.MARKET_SYMBOLS:
                    try:
                        total += self.sync_symbol(symbol, timeframe)
                    except Exception:
                        logger.exception(
                            "History sync failed for %s %s",
                            symbol,
                            timeframe,
                        )
            if total:
                logger.info("History sync inserted %d candles.", total)
            return total
        finally:
            self._lock.release()

    def sync_gaps_only(
        self,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
    ) -> int:
        """
        Fast reconnect path: only fill candles missing since the newest
        stored candle (no depth checks, no deep downloads).
        """

        if not mt5_client.initialize():
            return 0

        if not self._lock.acquire(blocking=False):
            return 0

        try:
            from app.database.database import SessionLocal
            from app.repositories.market_repository import MarketRepository

            total = 0
            for timeframe in timeframes or settings.MARKET_TIMEFRAMES:
                for symbol in symbols or settings.MARKET_SYMBOLS:
                    db = SessionLocal()
                    try:
                        repository = MarketRepository(db)
                        newest = repository.get_statistics(
                            symbol.upper(), timeframe.upper()
                        ).get("last_candle")
                        if newest is None:
                            continue
                        total += self._gap_sync(
                            db,
                            symbol.upper(),
                            timeframe.upper(),
                            to_utc(newest),
                        )
                    except Exception:
                        logger.exception(
                            "Gap sync failed for %s %s",
                            symbol,
                            timeframe,
                        )
                    finally:
                        db.close()
            if total:
                logger.info("Gap sync inserted %d candles.", total)
            return total
        finally:
            self._lock.release()

    # ------------------------------------------------------------------
    # Initial deep download
    # ------------------------------------------------------------------

    def _initial_sync(self, db, symbol: str, timeframe: str) -> int:
        """
        Download as much history as the broker provides, paging
        backwards with copy_rates_from_pos so repeated chunks never
        re-read the same newest bars.
        """

        mt5_timeframe = timeframe_to_mt5(timeframe)
        target = self._initial_target_bars(timeframe)
        chunk = max(1, min(int(settings.MARKET_COLLECTOR_BARS), target))

        logger.info(
            "Initial history sync %s %s (target=%d bars)",
            symbol,
            timeframe,
            target,
        )

        inserted = 0
        position = 0

        while position < target:
            pull = min(chunk, target - position)
            rates = mt5.copy_rates_from_pos(
                symbol,
                mt5_timeframe,
                position,
                pull,
            )
            if rates is None or len(rates) == 0:
                break

            inserted += self._store_rates(db, symbol, timeframe, rates)
            position += len(rates)

            if len(rates) < pull:
                break  # broker history exhausted

        logger.info(
            "Initial sync complete %s %s -> %d candles",
            symbol,
            timeframe,
            inserted,
        )
        return inserted

    @staticmethod
    def _initial_target_bars(timeframe: str) -> int:
        """
        Bars covering MARKET_INITIAL_SYNC_YEARS for a timeframe (actual
        depth is capped by broker history availability).
        """

        years = max(1, int(settings.MARKET_INITIAL_SYNC_YEARS))
        seconds = years * 365 * 24 * 3600
        return max(1, seconds // timeframe_seconds(timeframe))

    # ------------------------------------------------------------------
    # Gap fill
    # ------------------------------------------------------------------

    def _gap_sync(
        self,
        db,
        symbol: str,
        timeframe: str,
        newest_stored: datetime,
    ) -> int:
        """
        Download only completed candles newer than the newest stored
        candle. Each missed bucket becomes its own proper candle.
        """

        duration = timeframe_seconds(timeframe)
        start = newest_stored + timedelta(seconds=duration)
        # Generous future bound; MT5 simply returns up to the newest bar.
        end = datetime.now(tz=UTC) + timedelta(days=2)

        if start >= end:
            return 0

        mt5_timeframe = timeframe_to_mt5(timeframe)
        rates = mt5.copy_rates_range(
            symbol,
            mt5_timeframe,
            start,
            end,
        )

        if rates is None or len(rates) == 0:
            return 0

        return self._store_rates(db, symbol, timeframe, rates)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _store_rates(self, db, symbol: str, timeframe: str, rates) -> int:
        """
        Persist MT5 rate rows, excluding the still-forming bucket so
        completed candles in the database stay immutable.
        """

        from app.models.market_candle import MarketCandle
        from app.repositories.market_repository import MarketRepository

        forming_start = self._forming_bucket_start(symbol, timeframe)
        duration = timeframe_seconds(timeframe)

        candles: list[MarketCandle] = []
        for row in rates:
            bar_time = int(row["time"])
            if forming_start is not None and bar_time >= forming_start:
                continue  # exclude the live (incomplete) bar
            # Defensive: bar must align exactly to its bucket.
            if bar_time % duration != 0:
                bar_time = bucket_start_epoch(bar_time, timeframe)

            candles.append(
                MarketCandle(
                    symbol=symbol,
                    timeframe=timeframe,
                    time=epoch_to_datetime(bar_time),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    tick_volume=int(row["tick_volume"]),
                    spread=int(row["spread"]),
                    real_volume=int(row["real_volume"]),
                )
            )

        if not candles:
            return 0

        repository = MarketRepository(db)
        inserted = repository.bulk_create(candles)
        db.commit()
        return inserted

    def _forming_bucket_start(
        self,
        symbol: str,
        timeframe: str,
    ) -> int | None:
        """
        Bucket start (epoch seconds) of the currently forming candle,
        derived from the newest broker tick (broker/server time).
        """

        try:
            tick = mt5.symbol_info_tick(symbol)
        except Exception:
            tick = None

        if tick is None:
            return None

        tick_time = int(getattr(tick, "time", 0) or 0)
        if tick_time <= 0:
            return None

        return bucket_start_epoch(tick_time, timeframe)


history_synchronizer = HistorySynchronizer()
