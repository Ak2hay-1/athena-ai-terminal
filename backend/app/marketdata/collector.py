"""
Tick Collector.

Dedicated service that receives every live MT5 tick, normalizes it, and
passes it immediately to the Candle Engine. It never builds candles
itself.

Ticks are pulled with mt5.copy_ticks_from() using a per-symbol
time_msc cursor, so every broker tick is captured (unlike
symbol_info_tick polling, which only samples the newest tick).
Timestamps are broker/server time.
"""

from __future__ import annotations

import threading
import time as time_module
from datetime import UTC
from datetime import datetime
from typing import Callable

from app.core.logger import get_logger
from app.core.settings import settings
from app.marketdata.engine import CandleEngine
from app.marketdata.ticks import Tick
from app.mt5.client import mt5_client
from app.mt5.sdk import mt5

logger = get_logger("athena.marketdata.collector")

_COPY_TICKS_ALL = int(getattr(mt5, "COPY_TICKS_ALL", -1))


class TickCollector:
    """
    Polls MT5 for new ticks and forwards them to the candle engine.

    Automatic recovery: on MT5 failure the collector pauses, reconnects
    with exponential backoff, fires ``on_reconnected`` (so the gap
    synchronizer can heal missing candles), and resumes.
    """

    def __init__(
        self,
        engine: CandleEngine,
        symbols: list[str] | None = None,
        poll_ms: int | None = None,
        on_reconnected: Callable[[], None] | None = None,
    ) -> None:
        self.engine = engine
        self.symbols = [
            s.upper() for s in (symbols or settings.MARKET_SYMBOLS)
        ]
        self.poll_s = max(50, int(poll_ms or settings.TICK_POLL_MS)) / 1000.0
        self.on_reconnected = on_reconnected

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        # Per-symbol cursor: newest processed broker time_msc.
        self._cursors: dict[str, int] = {}
        self._fail_streak = 0
        self._was_connected = False
        self._ticks_collected = 0

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
            name="athena-tick-collector",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Tick collector started (poll=%.0fms symbols=%d)",
            self.poll_s * 1000,
            len(self.symbols),
        )

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=5.0)
            self._thread = None
        logger.info("Tick collector stopped.")

    def metrics(self) -> dict:
        return {
            "running": self.running,
            "symbols": self.symbols,
            "ticks_collected": self._ticks_collected,
            "mt5_connected": self._was_connected,
        }

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.is_set():
            if not self._ensure_connection():
                continue

            for symbol in self.symbols:
                if self._stop.is_set():
                    break
                try:
                    self._collect_symbol(symbol)
                except Exception:
                    logger.exception("Tick collection failed for %s", symbol)

            try:
                # Close forming candles whose bucket ended without a new
                # tick (quiet markets / session close).
                self.engine.close_expired_candles()
            except Exception:
                logger.exception("Expired-candle sweep failed")

            self._stop.wait(self.poll_s)

    def _ensure_connection(self) -> bool:
        if mt5_client.connected:
            if not self._was_connected:
                # Recovered from a disconnect: heal missing candles
                # before live processing resumes.
                self._was_connected = True
                self.engine.mark_discontinuity()
                self._notify_reconnected()
            return True

        if mt5_client.initialize():
            self._fail_streak = 0
            self._was_connected = True
            self.engine.mark_discontinuity()
            self._notify_reconnected()
            return True

        # Live updates paused; existing candles are kept untouched.
        self._was_connected = False
        self._fail_streak = min(self._fail_streak + 1, 6)
        wait_s = min(60.0, 2.0 ** self._fail_streak)
        if self._fail_streak <= 2 or self._fail_streak % 3 == 0:
            logger.warning(
                "Tick collector: MT5 unavailable; retry in %.0fs",
                wait_s,
            )
        self._stop.wait(wait_s)
        return False

    def _notify_reconnected(self) -> None:
        if self.on_reconnected is None:
            return
        try:
            self.on_reconnected()
        except Exception:
            logger.exception("on_reconnected hook failed")

    # ------------------------------------------------------------------
    # Per-symbol collection
    # ------------------------------------------------------------------

    def _collect_symbol(self, symbol: str) -> None:
        cursor = self._cursors.get(symbol)

        if cursor is None:
            # First poll: anchor the cursor at the newest broker tick so
            # historical ticks are not replayed into the engine.
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return
            time_msc = int(
                getattr(tick, "time_msc", 0)
                or int(getattr(tick, "time", 0) or 0) * 1000
            )
            if time_msc <= 0:
                return
            self._cursors[symbol] = time_msc - 1
            cursor = time_msc - 1

        batch_size = 2000
        processed_any = False

        # Drain in batches until caught up so bursts never fall behind.
        for _ in range(50):
            raw_ticks = mt5.copy_ticks_from(
                symbol,
                datetime.fromtimestamp(cursor / 1000.0, tz=UTC),
                batch_size,
                _COPY_TICKS_ALL,
            )

            if raw_ticks is None or len(raw_ticks) == 0:
                break

            newest = cursor
            for row in raw_ticks:
                time_msc = int(row["time_msc"])
                if time_msc <= cursor:
                    continue  # duplicate or already-processed tick

                tick = Tick(
                    symbol=symbol,
                    time_msc=time_msc,
                    bid=float(row["bid"] or 0),
                    ask=float(row["ask"] or 0),
                    last=float(row["last"] or 0),
                )
                if tick.price <= 0:
                    continue

                self.engine.process_tick(tick)
                self._ticks_collected += 1
                processed_any = True
                newest = max(newest, time_msc)

            if newest == cursor:
                break  # nothing new in this batch

            cursor = newest
            self._cursors[symbol] = newest

            if len(raw_ticks) < batch_size:
                break  # caught up

        if not processed_any:
            self._fallback_info_tick(symbol, cursor)

    def _fallback_info_tick(self, symbol: str, cursor: int) -> None:
        """
        Some brokers throttle copy_ticks_from; fall back to the newest
        tick snapshot so the live candle keeps updating.
        """

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return

        time_msc = int(
            getattr(tick, "time_msc", 0)
            or int(getattr(tick, "time", 0) or 0) * 1000
        )
        if time_msc <= cursor:
            return

        normalized = Tick(
            symbol=symbol,
            time_msc=time_msc,
            bid=float(getattr(tick, "bid", 0) or 0),
            ask=float(getattr(tick, "ask", 0) or 0),
            last=float(getattr(tick, "last", 0) or 0),
        )
        if normalized.price <= 0:
            return

        self.engine.process_tick(normalized)
        self._ticks_collected += 1
        self._cursors[symbol] = time_msc
