"""
Market Watch Agent — continuous scan via SystemTick, publish MarketUpdated.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from datetime import timezone
from typing import Any

from app.agents.base import BaseAgent
from app.agents.market_watch.publisher import MarketWatchPublisher
from app.agents.market_watch.scanner import PairState
from app.agents.market_watch.scanner import detect_changes
from app.agents.market_watch.scanner import normalize_watch_universe
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.market_watch")


class MarketWatchAgent(BaseAgent):
    id = "market_watch"
    name = "Market Watch Agent"
    version = "1.0.0"
    priority = 10
    subscribed_events = [EventType.SYSTEM_TICK]

    def __init__(self) -> None:
        super().__init__()
        self._pair_state: dict[tuple[str, str], PairState] = {}
        self._watch_publisher: MarketWatchPublisher | None = None
        self._last_scan_at: datetime | None = None
        self._last_scan_mono: float = 0.0
        self._events_created: int = 0
        self._scan_count: int = 0
        self._scan_runtime_ms: float = 0.0
        self._scan_errors: int = 0

    async def initialize(self) -> None:
        await super().initialize()
        publisher = self._publisher
        if publisher is None:
            publisher = EventPublisher()
        self._watch_publisher = MarketWatchPublisher(publisher)
        logger.info(
            "agent=%s action=initialize symbols=%s timeframes=%s",
            self.id,
            list(settings.MARKET_WATCH_SYMBOLS),
            list(settings.MARKET_WATCH_TIMEFRAMES),
        )

    async def handle_event(self, event: Event) -> None:
        if str(event.type) != EventType.SYSTEM_TICK:
            return

        interval = max(1, int(settings.MARKET_WATCH_SCAN_INTERVAL_SECONDS))
        now_mono = time.monotonic()
        if self._last_scan_mono and (now_mono - self._last_scan_mono) < interval:
            return

        await self._run_scan()

    async def _run_scan(self) -> None:
        if self._tool_manager is None or self._watch_publisher is None:
            logger.warning("agent=%s action=scan status=not_ready", self.id)
            return

        started = time.perf_counter()
        symbols, timeframes = normalize_watch_universe()
        events_generated = 0

        try:
            result = await self._tool_manager.execute(
                "market_data",
                action="batch_candles",
                symbols=symbols,
                timeframes=timeframes,
                limit=settings.MARKET_WATCH_CANDLE_LIMIT,
            )
            data = result.get("data") or {}

            for symbol in symbols:
                for timeframe in timeframes:
                    candles = (data.get(symbol) or {}).get(timeframe) or []
                    if not candles:
                        continue

                    key = (symbol, timeframe)
                    state = self._pair_state.setdefault(key, PairState())

                    changes = await asyncio.to_thread(
                        detect_changes,
                        symbol=symbol,
                        timeframe=timeframe,
                        candles=candles,
                        state=state,
                    )

                    for change in changes:
                        published = await self._watch_publisher.publish_change(change)
                        if published:
                            events_generated += 1

            self._events_created += events_generated
            self._scan_count += 1
            self._last_scan_at = datetime.now(timezone.utc)
            self._last_scan_mono = time.monotonic()
            duration_ms = (time.perf_counter() - started) * 1000
            self._scan_runtime_ms += duration_ms

            try:
                from app.services.scanner_state import scanner_state

                scanner_state.mark_scan(
                    at=self._last_scan_at,
                    universe_size=len(symbols) * len(timeframes),
                )
            except Exception:
                logger.exception(
                    "agent=%s action=scan status=scanner_state_failed",
                    self.id,
                )

            logger.info(
                "agent=%s action=scan status=ok symbols_scanned=%s "
                "timeframes=%s events_generated=%s scan_duration_ms=%.2f",
                self.id,
                len(symbols),
                len(timeframes),
                events_generated,
                duration_ms,
            )
        except Exception:
            self._scan_errors += 1
            logger.exception("agent=%s action=scan status=error", self.id)
            raise

    def health(self) -> dict[str, Any]:
        base = super().health()
        avg_scan = (
            self._scan_runtime_ms / self._scan_count if self._scan_count else 0.0
        )
        base.update(
            {
                "last_scan": (
                    self._last_scan_at.isoformat() if self._last_scan_at else None
                ),
                "events_created": self._events_created,
                "average_runtime": avg_scan,
                "errors": self._scan_errors,
                "scan_count": self._scan_count,
                "duplicates_skipped": (
                    self._watch_publisher.duplicates_skipped
                    if self._watch_publisher
                    else 0
                ),
            }
        )
        return base

    def metrics(self) -> dict[str, Any]:
        base = super().metrics()
        base.update(
            {
                "events_created": self._events_created,
                "scan_count": self._scan_count,
                "scan_errors": self._scan_errors,
            }
        )
        return base
