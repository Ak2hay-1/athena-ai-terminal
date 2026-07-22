"""
SMC Agent — runs after TechnicalAnalysisCompleted; evidence only.
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from typing import Any

from app.agents.base import BaseAgent
from app.agents.smc.analyzer import analyze_smc
from app.agents.technical.indicators import candles_to_dataframe
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.smc")


class SmcAgent(BaseAgent):
    id = "smc"
    name = "SMC Agent"
    version = "1.0.0"
    priority = 30
    subscribed_events = [EventType.TECHNICAL_ANALYSIS_COMPLETED]

    def __init__(self) -> None:
        super().__init__()
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._analyses_completed = 0

    def _key(self, symbol: str, timeframe: str, candle_time: str) -> str:
        return f"{symbol}|{timeframe}|{candle_time}"

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def _cache_put(self, key: str, value: dict[str, Any]) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        max_size = max(1, int(settings.SMC_INDICATOR_CACHE_SIZE))
        while len(self._cache) > max_size:
            self._cache.popitem(last=False)

    async def handle_event(self, event: Event) -> None:
        if str(event.type) != EventType.TECHNICAL_ANALYSIS_COMPLETED:
            return
        if self._tool_manager is None:
            logger.warning("agent=%s action=analyze status=no_tools", self.id)
            return

        payload = event.payload or {}
        symbol = str(payload.get("symbol", "")).upper()
        timeframe = str(payload.get("timeframe", "")).upper()
        candle_time = str(payload.get("candle_time") or payload.get("timestamp") or "")
        if not symbol or not timeframe:
            return

        cache_key = self._key(symbol, timeframe, candle_time)
        if self._cache_get(cache_key) is not None:
            return

        started = time.perf_counter()
        result = await self._tool_manager.execute(
            "market_data",
            action="get_latest_candles",
            symbol=symbol,
            timeframe=timeframe,
            limit=settings.MARKET_WATCH_CANDLE_LIMIT,
        )
        candles = result.get("candles") or []
        if len(candles) < 30:
            logger.info(
                "agent=%s action=analyze status=insufficient_data symbol=%s count=%s",
                self.id,
                symbol,
                len(candles),
            )
            return

        def _compute() -> dict[str, Any]:
            df = candles_to_dataframe(candles)
            evidence = analyze_smc(df)
            evidence.update(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "candle_time": candle_time,
                    "technical_score": payload.get("score"),
                    "source_event_id": event.id,
                }
            )
            return evidence

        analysis = await asyncio.to_thread(_compute)
        self._cache_put(cache_key, analysis)
        self._analyses_completed += 1

        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=analyze status=ok symbol=%s timeframe=%s score=%s "
            "duration_ms=%.2f",
            self.id,
            symbol,
            timeframe,
            analysis.get("score"),
            duration_ms,
        )

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.SMC_ANALYSIS_COMPLETED,
            source=self.id,
            payload=analysis,
            correlation_id=event.correlation_id or event.id,
            metadata={"source_event_id": event.id},
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update(
            {
                "analyses_completed": self._analyses_completed,
                "cache_size": len(self._cache),
            }
        )
        return base
