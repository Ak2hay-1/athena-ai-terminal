"""
Persistence Writer.

Batched, reliable database writes for the market data engine.

Completed candles are queued and flushed to PostgreSQL in small
batches (immutable — ON CONFLICT DO NOTHING). Raw ticks are optionally
persisted for backtesting / future ML. Database failures never lose
queued candles: batches are retained and retried with backoff.
"""

from __future__ import annotations

import queue
import threading

from app.core.logger import get_logger
from app.marketdata.engine import Candle
from app.marketdata.ticks import Tick
from app.marketdata.timeframes import epoch_to_datetime

logger = get_logger("athena.marketdata.persistence")


def _spread_points(symbol: str, spread_price: float) -> int:
    """Convert a price-unit spread to integer broker points."""

    if spread_price <= 0:
        return 0

    from app.core.settings import settings

    profile = settings.INSTRUMENT_RISK_PROFILES.get(symbol.upper(), {})
    tick_size = float(profile.get("tick_size") or 0.00001)
    if tick_size <= 0:
        tick_size = 0.00001
    return int(round(spread_price / tick_size))


class PersistenceWriter:
    """
    Background writer thread with bounded queues and batch flushing.
    """

    def __init__(
        self,
        *,
        flush_interval_s: float = 1.0,
        max_batch: int = 500,
        store_ticks: bool = False,
    ) -> None:
        self.flush_interval_s = flush_interval_s
        self.max_batch = max_batch
        self.store_ticks = store_ticks

        self._candles: queue.Queue = queue.Queue(maxsize=100_000)
        self._ticks: queue.Queue = queue.Queue(maxsize=500_000)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._candles_written = 0
        self._ticks_written = 0
        self._write_failures = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="athena-market-writer",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Market persistence writer started (ticks=%s)",
            self.store_ticks,
        )

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=10.0)
            self._thread = None
        # Final synchronous flush so completed candles survive shutdown.
        try:
            self._flush()
        except Exception:
            logger.exception("Final persistence flush failed")
        logger.info("Market persistence writer stopped.")

    def metrics(self) -> dict:
        return {
            "running": self.running,
            "candles_pending": self._candles.qsize(),
            "ticks_pending": self._ticks.qsize(),
            "candles_written": self._candles_written,
            "ticks_written": self._ticks_written,
            "write_failures": self._write_failures,
        }

    # ------------------------------------------------------------------
    # Producers (called from engine threads)
    # ------------------------------------------------------------------

    def enqueue_candle(self, candle: Candle) -> None:
        try:
            self._candles.put_nowait(candle)
        except queue.Full:
            self._write_failures += 1
            logger.error(
                "Candle write queue full; dropping %s %s %s",
                candle.symbol,
                candle.timeframe,
                candle.bucket_start,
            )

    def enqueue_tick(self, tick: Tick) -> None:
        if not self.store_ticks:
            return
        try:
            self._ticks.put_nowait(tick)
        except queue.Full:
            # Tick storage is best-effort; never block the tick path.
            pass

    # ------------------------------------------------------------------
    # Writer loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        backoff = 0.0
        while not self._stop.is_set():
            self._stop.wait(self.flush_interval_s + backoff)
            try:
                self._flush()
                backoff = 0.0
            except Exception:
                self._write_failures += 1
                backoff = min(30.0, (backoff or 1.0) * 2)
                logger.exception(
                    "Market data flush failed; retrying in %.0fs",
                    self.flush_interval_s + backoff,
                )

    def _flush(self) -> None:
        candles = self._drain(self._candles, self.max_batch)
        ticks = self._drain(self._ticks, self.max_batch * 10)

        if not candles and not ticks:
            return

        from app.database.database import SessionLocal

        db = SessionLocal()
        try:
            if candles:
                self._write_candles(db, candles)
            if ticks:
                self._write_ticks(db, ticks)
            db.commit()
        except Exception:
            db.rollback()
            # Re-queue so nothing is lost across DB outages.
            for candle in candles:
                self.enqueue_candle(candle)
            if self.store_ticks:
                for tick in ticks:
                    self.enqueue_tick(tick)
            raise
        finally:
            db.close()

    @staticmethod
    def _drain(source: queue.Queue, limit: int) -> list:
        items = []
        while len(items) < limit:
            try:
                items.append(source.get_nowait())
            except queue.Empty:
                break
        return items

    def _write_candles(self, db, candles: list[Candle]) -> None:
        from sqlalchemy.dialects.postgresql import insert

        from app.models.market_candle import MarketCandle

        rows = [
            {
                "symbol": candle.symbol,
                "timeframe": candle.timeframe,
                "time": epoch_to_datetime(candle.bucket_start),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "tick_volume": candle.tick_volume,
                "spread": _spread_points(candle.symbol, candle.spread),
                "real_volume": 0,
            }
            for candle in candles
        ]

        stmt = (
            insert(MarketCandle)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_market_candle")
        )
        result = db.execute(stmt)
        self._candles_written += result.rowcount or 0

    def _write_ticks(self, db, ticks: list[Tick]) -> None:
        from sqlalchemy.dialects.postgresql import insert

        from app.models.market_tick import MarketTick

        rows = [
            {
                "symbol": tick.symbol,
                "time": epoch_to_datetime(tick.epoch_seconds),
                "time_msc": tick.time_msc,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": tick.last,
                "spread": tick.spread,
            }
            for tick in ticks
        ]

        stmt = (
            insert(MarketTick)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_market_tick")
        )
        result = db.execute(stmt)
        self._ticks_written += result.rowcount or 0
