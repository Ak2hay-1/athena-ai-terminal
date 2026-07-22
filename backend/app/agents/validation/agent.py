"""
Validation Agent — buffers Technical + SMC + Risk; publishes TradeValidationCompleted.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

from app.agents.base import BaseAgent
from app.agents.validation.validator import validate_trade_evidence
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.validation")


class ValidationAgent(BaseAgent):
    id = "validation"
    name = "Validation Agent"
    version = "1.0.0"
    priority = 50
    subscribed_events = [
        EventType.TECHNICAL_ANALYSIS_COMPLETED,
        EventType.SMC_ANALYSIS_COMPLETED,
        EventType.RISK_ASSESSMENT_COMPLETED,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._buffer: dict[str, dict[str, Any]] = {}
        self._published: OrderedDict[str, None] = OrderedDict()
        self._validations = 0

    def _key(self, symbol: str, timeframe: str, candle_time: str) -> str:
        return f"{symbol}|{timeframe}|{candle_time}"

    def _mark_published(self, key: str) -> None:
        self._published[key] = None
        self._published.move_to_end(key)
        max_size = max(1, int(settings.VALIDATION_CACHE_SIZE))
        while len(self._published) > max_size:
            self._published.popitem(last=False)

    async def handle_event(self, event: Event) -> None:
        payload = event.payload or {}
        symbol = str(payload.get("symbol", "")).upper()
        timeframe = str(payload.get("timeframe", "")).upper()
        candle_time = str(payload.get("candle_time") or payload.get("timestamp") or "")
        if not symbol or not timeframe or not candle_time:
            return

        key = self._key(symbol, timeframe, candle_time)
        if key in self._published:
            return

        slot = self._buffer.setdefault(key, {})
        event_type = str(event.type)
        if event_type == EventType.TECHNICAL_ANALYSIS_COMPLETED:
            slot["technical"] = payload
        elif event_type == EventType.SMC_ANALYSIS_COMPLETED:
            slot["smc"] = payload
        elif event_type == EventType.RISK_ASSESSMENT_COMPLETED:
            slot["risk"] = payload
        else:
            return

        slot["correlation_id"] = (
            slot.get("correlation_id") or event.correlation_id or event.id
        )

        if not all(k in slot for k in ("technical", "smc", "risk")):
            return

        await self._validate(key, symbol, timeframe, candle_time, slot)

    async def _validate(
        self,
        key: str,
        symbol: str,
        timeframe: str,
        candle_time: str,
        slot: dict[str, Any],
    ) -> None:
        started = time.perf_counter()
        technical = slot["technical"]
        smc = slot["smc"]
        risk = slot["risk"]

        result = validate_trade_evidence(
            technical_score=float(technical.get("score") or 0),
            smc_score=float(smc.get("score") or 0),
            risk_score=float(risk.get("risk_score") or 0),
            risk_reward=float(risk.get("risk_reward") or 0),
            warnings=list(risk.get("warnings") or []),
        )

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_time": candle_time,
            "status": result["status"],
            "confluence": result["confluence"],
            "validation_score": result["validation_score"],
            "approval": result["approval"],
            "reasons": result["reasons"],
            "scores": result["scores"],
        }

        self._mark_published(key)
        self._buffer.pop(key, None)
        self._validations += 1

        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=validate status=%s symbol=%s confluence=%s "
            "duration_ms=%.2f reasons=%s",
            self.id,
            payload["status"],
            symbol,
            payload["confluence"],
            duration_ms,
            payload["reasons"],
        )

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.TRADE_VALIDATION_COMPLETED,
            source=self.id,
            payload=payload,
            correlation_id=slot.get("correlation_id"),
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update(
            {
                "validations_completed": self._validations,
                "buffer_size": len(self._buffer),
            }
        )
        return base
