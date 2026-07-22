"""
Candle Engine.

Builds OHLC candles from live ticks using strict UTC time buckets.

Rules:
- The first tick of a bucket sets open = high = low = close = price.
- Every later tick updates high/low/close only; open never changes.
- A candle closes when (and only when) broker time crosses its bucket
  boundary — never because of restarts, UI refreshes, or reconnects.
- Closed candles are immutable. Missed periods are never merged into an
  oversized candle; gaps are healed separately by the history
  synchronizer using MT5 backfill.
"""

from __future__ import annotations

import threading
import time as time_module
from dataclasses import dataclass
from typing import Callable

from app.core.logger import get_logger
from app.marketdata.ticks import Tick
from app.marketdata.timeframes import bucket_start_epoch
from app.marketdata.timeframes import epoch_to_datetime
from app.marketdata.timeframes import timeframe_seconds

logger = get_logger("athena.marketdata.engine")


@dataclass(slots=True)
class Candle:
    """A candle under construction or just closed."""

    symbol: str
    timeframe: str
    bucket_start: int  # epoch seconds, UTC — candle open time
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: float = 0.0
    complete: bool = False
    # True when the engine may have missed earlier ticks of this bucket
    # (startup / reconnect mid-bucket). Partial candles are never
    # persisted; the gap synchronizer fills the true bar from MT5.
    partial: bool = False
    last_tick_msc: int = 0

    @property
    def bucket_end(self) -> int:
        return self.bucket_start + timeframe_seconds(self.timeframe)

    def to_payload(self) -> dict:
        """Serialize for WebSocket / Redis consumers."""

        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "time": epoch_to_datetime(self.bucket_start).isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "tick_volume": self.tick_volume,
            "spread": self.spread,
            "complete": self.complete,
            "partial": self.partial,
        }


class CandleBuilder:
    """
    Stateful OHLC builder for one (symbol, timeframe) pair.

    Not thread-safe by itself; CandleEngine serializes access.
    """

    def __init__(self, symbol: str, timeframe: str) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.current: Candle | None = None
        # Newest completed bucket start; ticks at or before this bucket
        # can never reopen a closed candle.
        self._floor: int | None = None
        # The first candle after startup/reconnect may have missed the
        # beginning of its bucket, so it is flagged partial.
        self._next_partial = True

    def seed(self, bucket_start: int) -> None:
        """
        Mark the last known completed bucket so stale ticks (older than
        already-persisted history) can never reopen closed candles.
        """

        if self.current is None:
            self._floor = bucket_start
        # If a forming candle already exists, history is behind us.

    def apply_tick(self, tick: Tick) -> Candle | None:
        """
        Apply a tick. Returns the completed candle when the tick opens a
        new bucket, otherwise None.
        """

        price = tick.price
        if price <= 0:
            return None

        bucket = bucket_start_epoch(tick.epoch_seconds, self.timeframe)

        if self.current is None:
            if self._floor is not None and bucket <= self._floor:
                # Tick belongs to an already-completed historical bucket.
                return None
            self.current = self._new_candle(bucket, tick, price)
            return None

        current = self.current

        if bucket == current.bucket_start:
            # Duplicate / same-bucket tick: update mutable fields only.
            if tick.time_msc < current.last_tick_msc:
                # Out-of-order tick inside the same bucket: still safe
                # to extend high/low, but do not step close backwards.
                current.high = max(current.high, price)
                current.low = min(current.low, price)
                current.tick_volume += 1
                return None
            current.high = max(current.high, price)
            current.low = min(current.low, price)
            current.close = price
            current.spread = tick.spread
            current.tick_volume += 1
            current.last_tick_msc = tick.time_msc
            return None

        if bucket < current.bucket_start:
            # Stale tick from a closed bucket — closed candles are
            # immutable, so drop it.
            return None

        # Boundary crossed: freeze the current candle and open a new one.
        # Any skipped buckets in between stay empty (no ticks -> no
        # candle) and are healed by the gap synchronizer if MT5 has data.
        closed = current
        closed.complete = True
        self._floor = closed.bucket_start
        self.current = self._new_candle(bucket, tick, price)
        return closed

    def close_expired(self, broker_now_epoch: float) -> Candle | None:
        """
        Close the forming candle purely by time when its bucket has
        ended but no tick has arrived in the next bucket yet.
        """

        current = self.current
        if current is None:
            return None
        if broker_now_epoch < current.bucket_end:
            return None

        current.complete = True
        self.current = None
        self._floor = current.bucket_start
        return current

    def mark_discontinuity(self) -> None:
        """
        Tick continuity was lost (MT5 disconnect). The forming candle
        and the next opened candle may both be missing ticks.
        """

        if self.current is not None:
            self.current.partial = True
        self._next_partial = True

    def _new_candle(self, bucket: int, tick: Tick, price: float) -> Candle:
        partial = self._next_partial
        self._next_partial = False
        return Candle(
            symbol=self.symbol,
            timeframe=self.timeframe,
            bucket_start=bucket,
            open=price,
            high=price,
            low=price,
            close=price,
            tick_volume=1,
            spread=tick.spread,
            partial=partial,
            last_tick_msc=tick.time_msc,
        )


@dataclass(slots=True)
class EngineCallbacks:
    """Hooks fired by the engine (all invoked on engine threads)."""

    on_candle_closed: Callable[[Candle], None] | None = None
    on_candle_forming: Callable[[Candle], None] | None = None
    on_tick: Callable[[Tick], None] | None = None


class CandleEngine:
    """
    Thread-safe multi-symbol, multi-timeframe candle engine.

    One instance serves every configured symbol. Per-symbol locks keep
    contention low while supporting thousands of ticks per second.
    """

    def __init__(
        self,
        timeframes: list[str] | None = None,
        callbacks: EngineCallbacks | None = None,
    ) -> None:
        self.timeframes = [tf.upper() for tf in (timeframes or ["M1"])]
        self.callbacks = callbacks or EngineCallbacks()
        self._builders: dict[str, dict[str, CandleBuilder]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._registry_lock = threading.Lock()
        # Broker clock offset: broker_epoch - local_epoch, updated on
        # every tick so expiry checks use broker time even between ticks.
        self._clock_offset: float = 0.0
        self._ticks_processed = 0
        self._candles_closed = 0

    # ------------------------------------------------------------------
    # Tick path
    # ------------------------------------------------------------------

    def process_tick(self, tick: Tick) -> list[Candle]:
        """
        Feed one tick through every timeframe builder for its symbol.

        Returns candles closed by this tick (already reported through
        callbacks as well).
        """

        symbol = tick.symbol.upper()
        lock, builders = self._get_symbol_state(symbol)

        closed: list[Candle] = []

        with lock:
            self._clock_offset = tick.epoch_seconds - time_module.time()

            for builder in builders.values():
                candle = builder.apply_tick(tick)
                if candle is not None:
                    closed.append(candle)

            forming = [
                builder.current
                for builder in builders.values()
                if builder.current is not None
            ]

        self._ticks_processed += 1
        self._candles_closed += len(closed)

        if self.callbacks.on_tick is not None:
            self._safe(self.callbacks.on_tick, tick)

        for candle in closed:
            if self.callbacks.on_candle_closed is not None:
                self._safe(self.callbacks.on_candle_closed, candle)

        if self.callbacks.on_candle_forming is not None:
            for candle in forming:
                self._safe(self.callbacks.on_candle_forming, candle)

        return closed

    # ------------------------------------------------------------------
    # Time-based closing (no-tick boundaries)
    # ------------------------------------------------------------------

    def close_expired_candles(self) -> list[Candle]:
        """
        Close forming candles whose bucket has ended (broker time),
        even when no new tick has arrived. Called periodically.
        """

        broker_now = self.broker_now()
        closed: list[Candle] = []

        with self._registry_lock:
            symbols = list(self._builders)

        for symbol in symbols:
            lock, builders = self._get_symbol_state(symbol)
            with lock:
                for builder in builders.values():
                    candle = builder.close_expired(broker_now)
                    if candle is not None:
                        closed.append(candle)

        self._candles_closed += len(closed)

        for candle in closed:
            if self.callbacks.on_candle_closed is not None:
                self._safe(self.callbacks.on_candle_closed, candle)

        return closed

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    def current_candle(self, symbol: str, timeframe: str) -> Candle | None:
        symbol = symbol.upper()
        timeframe = timeframe.upper()
        lock, builders = self._get_symbol_state(symbol)
        with lock:
            builder = builders.get(timeframe)
            return builder.current if builder else None

    def seed_last_completed(
        self,
        symbol: str,
        timeframe: str,
        bucket_start_epoch_s: int,
    ) -> None:
        """
        Inform the engine of the newest completed candle in storage so
        late ticks can never regenerate already-persisted buckets.
        """

        lock, builders = self._get_symbol_state(symbol.upper())
        with lock:
            builder = builders.get(timeframe.upper())
            if builder is not None:
                builder.seed(bucket_start_epoch_s)

    def mark_discontinuity(self) -> None:
        """
        Flag every builder after a tick-stream interruption so affected
        candles are treated as partial (healed from MT5, not persisted
        from incomplete tick data).
        """

        with self._registry_lock:
            symbols = list(self._builders)

        for symbol in symbols:
            lock, builders = self._get_symbol_state(symbol)
            with lock:
                for builder in builders.values():
                    builder.mark_discontinuity()

    def broker_now(self) -> float:
        """Best-known broker time (epoch seconds)."""

        return time_module.time() + self._clock_offset

    def metrics(self) -> dict:
        return {
            "ticks_processed": self._ticks_processed,
            "candles_closed": self._candles_closed,
            "symbols": len(self._builders),
            "timeframes": self.timeframes,
            "clock_offset_seconds": round(self._clock_offset, 3),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_symbol_state(
        self,
        symbol: str,
    ) -> tuple[threading.Lock, dict[str, CandleBuilder]]:
        builders = self._builders.get(symbol)
        lock = self._locks.get(symbol)
        if builders is not None and lock is not None:
            return lock, builders

        with self._registry_lock:
            builders = self._builders.get(symbol)
            lock = self._locks.get(symbol)
            if builders is None or lock is None:
                builders = {
                    tf: CandleBuilder(symbol, tf) for tf in self.timeframes
                }
                lock = threading.Lock()
                self._builders[symbol] = builders
                self._locks[symbol] = lock
            return lock, builders

    @staticmethod
    def _safe(callback: Callable, *args) -> None:
        try:
            callback(*args)
        except Exception:
            logger.exception("Candle engine callback failed")
