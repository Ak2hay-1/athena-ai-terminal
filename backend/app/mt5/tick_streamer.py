"""
High-frequency MT5 tick → WebSocket streamer.
"""

from __future__ import annotations

import threading
from datetime import datetime
from datetime import timezone

from app.core.logger import logger
from app.core.settings import settings
from app.mt5.client import mt5_client
from app.mt5.sdk import mt5
from app.services.websocket_broadcast import broadcast_tick_update


class TickStreamer:
    """
    Polls MT5 symbol_info_tick for MARKET_SYMBOLS and broadcasts
    unchanged-skipped ticks over the market WebSocket.
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last: dict[str, tuple[float, float, float]] = {}
        self._mt5_fail_streak = 0

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if not settings.TICK_STREAM_ENABLED:
            logger.info("Tick streamer disabled (TICK_STREAM_ENABLED=false).")
            return

        if self.running:
            return

        self._stop.clear()
        self._mt5_fail_streak = 0
        self._thread = threading.Thread(
            target=self._run,
            name="mt5-tick-streamer",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "Tick streamer started (poll=%dms symbols=%d)",
            max(50, int(settings.TICK_POLL_MS)),
            len(settings.MARKET_SYMBOLS),
        )

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=5.0)
            self._thread = None
        self._last.clear()
        self._mt5_fail_streak = 0
        logger.info("Tick streamer stopped.")

    def _run(self) -> None:
        poll_s = max(50, int(settings.TICK_POLL_MS)) / 1000.0

        while not self._stop.is_set():
            if not mt5_client.connected:
                if not mt5_client.initialize():
                    # Exponential backoff so failed IPC cannot starve the API.
                    self._mt5_fail_streak = min(self._mt5_fail_streak + 1, 6)
                    wait_s = min(60.0, 2.0 ** self._mt5_fail_streak)
                    if self._mt5_fail_streak <= 2 or self._mt5_fail_streak % 3 == 0:
                        logger.warning(
                            "Tick streamer: MT5 unavailable; retry in %.0fs",
                            wait_s,
                        )
                    self._stop.wait(wait_s)
                    continue
                self._mt5_fail_streak = 0

            for symbol in settings.MARKET_SYMBOLS:
                if self._stop.is_set():
                    break
                self._emit_tick(str(symbol).upper())

            self._stop.wait(poll_s)

    def _emit_tick(self, symbol: str) -> None:
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return

            bid = float(getattr(tick, "bid", 0) or 0)
            ask = float(getattr(tick, "ask", 0) or 0)
            mid = (bid + ask) / 2.0 if bid and ask else (bid or ask)
            if not mid:
                return

            prev = self._last.get(symbol)
            if prev is not None and prev == (bid, ask, mid):
                return

            self._last[symbol] = (bid, ask, mid)

            raw_time = getattr(tick, "time", None)
            time_iso: str | None = None
            if raw_time:
                try:
                    time_iso = datetime.fromtimestamp(
                        int(raw_time),
                        tz=timezone.utc,
                    ).isoformat()
                except (TypeError, ValueError, OSError):
                    time_iso = None

            broadcast_tick_update(
                symbol=symbol,
                bid=bid,
                ask=ask,
                mid=mid,
                time=time_iso,
            )
        except Exception:
            logger.exception("Tick stream failed for %s", symbol)


tick_streamer = TickStreamer()
