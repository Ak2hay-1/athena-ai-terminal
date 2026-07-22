"""
Technical Analysis Agent — reacts to MarketUpdated only.
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from typing import Any

from app.agents.base import BaseAgent
from app.agents.technical.analyzer import analyze
from app.agents.technical.indicators import candles_to_dataframe
from app.agents.technical.scorer import score_technical
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.technical")


class TechnicalAgent(BaseAgent):
    id = "technical"
    name = "Technical Agent"
    version = "1.0.0"
    priority = 20
    subscribed_events = [EventType.MARKET_UPDATED]

    def __init__(self) -> None:
        super().__init__()
        self._cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._analyses_completed: int = 0

    def _cache_key(self, symbol: str, timeframe: str, candle_time: str) -> str:
        return f"{symbol}|{timeframe}|{candle_time}"

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def _cache_put(self, key: str, value: dict[str, Any]) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        max_size = max(1, int(settings.TECHNICAL_INDICATOR_CACHE_SIZE))
        while len(self._cache) > max_size:
            self._cache.popitem(last=False)

    async def handle_event(self, event: Event) -> None:
        if str(event.type) != EventType.MARKET_UPDATED:
            return
        if self._tool_manager is None:
            logger.warning("agent=%s action=analyze status=no_tools", self.id)
            return

        payload = event.payload or {}
        symbol = str(payload.get("symbol", "")).upper()
        timeframe = str(payload.get("timeframe", "")).upper()
        candle_time = str(payload.get("timestamp") or "")
        if not symbol or not timeframe:
            return

        # Skip duplicate work for the same candle (multiple MarketUpdated reasons)
        cache_key = self._cache_key(symbol, timeframe, candle_time)
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
                "agent=%s action=analyze status=insufficient_data symbol=%s "
                "timeframe=%s count=%s",
                self.id,
                symbol,
                timeframe,
                len(candles),
            )
            return

        def _compute() -> dict[str, Any]:
            df = candles_to_dataframe(candles)
            snapshot = analyze(df)
            snapshot.pop("dataframe", None)
            technical_score = score_technical(snapshot)
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "indicators": snapshot.get("indicators") or {},
                "score": technical_score,
                "trend": snapshot.get("trend"),
                "strength": snapshot.get("trend_strength"),
                "support": snapshot.get("support"),
                "resistance": snapshot.get("resistance"),
                "momentum": snapshot.get("momentum"),
                "atr": snapshot.get("atr"),
                "volume": snapshot.get("volume"),
                "ema_alignment": snapshot.get("ema_alignment"),
                "price": snapshot.get("price"),
                "source_event_id": event.id,
                "candle_time": candle_time,
            }

        analysis = await asyncio.to_thread(_compute)
        self._cache_put(cache_key, analysis)
        self._analyses_completed += 1

        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=analyze status=ok symbol=%s timeframe=%s "
            "score=%s duration_ms=%.2f",
            self.id,
            symbol,
            timeframe,
            analysis["score"],
            duration_ms,
        )
        await self._publish_result(analysis, event)

    async def _publish_result(
        self,
        analysis: dict[str, Any],
        source_event: Event,
    ) -> None:
        publisher = self._publisher
        if publisher is None:
            publisher = EventPublisher()

        await publisher.publish(
            EventType.TECHNICAL_ANALYSIS_COMPLETED,
            source=self.id,
            payload=analysis,
            correlation_id=source_event.correlation_id or source_event.id,
            metadata={"source_event_id": source_event.id},
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
