"""
Risk Agent — buffers Technical + SMC evidence, publishes RiskAssessmentCompleted.
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from typing import Any

from app.agents.base import BaseAgent
from app.agents.risk.analyzer import analyze_market_state
from app.agents.risk.calculator import calculate_risk_geometry
from app.agents.risk.scorer import score_risk
from app.core.logger import get_logger
from app.core.settings import settings
from app.database.database import SessionLocal
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.services.news_service import NewsService

logger = get_logger("athena.agents.risk")


def _fetch_news_context(symbol: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        return NewsService(db).get_context_for_symbol(symbol)
    except Exception:
        logger.exception("risk_agent action=news_context symbol=%s status=error", symbol)
        return {"high_impact_upcoming": False, "score": 0}
    finally:
        db.close()


class RiskAgent(BaseAgent):
    id = "risk"
    name = "Risk Agent"
    version = "1.0.0"
    priority = 40
    subscribed_events = [
        EventType.TECHNICAL_ANALYSIS_COMPLETED,
        EventType.SMC_ANALYSIS_COMPLETED,
    ]

    def __init__(self) -> None:
        super().__init__()
        self._buffer: dict[str, dict[str, Any]] = {}
        self._published: OrderedDict[str, None] = OrderedDict()
        self._assessments = 0

    def _key(self, symbol: str, timeframe: str, candle_time: str) -> str:
        return f"{symbol}|{timeframe}|{candle_time}"

    def _mark_published(self, key: str) -> None:
        self._published[key] = None
        self._published.move_to_end(key)
        max_size = max(1, int(settings.RISK_CACHE_SIZE))
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
        if str(event.type) == EventType.TECHNICAL_ANALYSIS_COMPLETED:
            slot["technical"] = payload
            slot["correlation_id"] = event.correlation_id or event.id
        elif str(event.type) == EventType.SMC_ANALYSIS_COMPLETED:
            slot["smc"] = payload
            slot["correlation_id"] = (
                slot.get("correlation_id") or event.correlation_id or event.id
            )
        else:
            return

        if "technical" not in slot or "smc" not in slot:
            return

        await self._assess(key, symbol, timeframe, candle_time, slot)

    async def _assess(
        self,
        key: str,
        symbol: str,
        timeframe: str,
        candle_time: str,
        slot: dict[str, Any],
    ) -> None:
        if self._tool_manager is None:
            logger.warning("agent=%s action=assess status=no_tools", self.id)
            return

        started = time.perf_counter()
        technical = slot["technical"]
        smc = slot["smc"]

        candles_result = await self._tool_manager.execute(
            "market_data",
            action="get_latest_candles",
            symbol=symbol,
            timeframe=timeframe,
            limit=settings.MARKET_WATCH_CANDLE_LIMIT,
        )
        candles = candles_result.get("candles") or []
        latest_result = await self._tool_manager.execute(
            "market_data",
            action="get_latest",
            symbol=symbol,
            timeframe=timeframe,
        )
        candle = latest_result.get("candle")
        news_context = await asyncio.to_thread(_fetch_news_context, symbol)

        def _compute() -> dict[str, Any]:
            geometry = calculate_risk_geometry(
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
                technical=technical,
            )
            market_state = analyze_market_state(
                symbol=symbol,
                candle=candle,
                atr_ratio=float(geometry.get("atr_ratio") or 1.0),
                news_context=news_context,
                geometry=geometry,
                smc=smc,
            )
            risk_score = score_risk(geometry=geometry, market_state=market_state)
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "candle_time": candle_time,
                "risk_score": risk_score,
                "recommended_stop_loss": geometry.get("recommended_stop_loss"),
                "recommended_take_profit": geometry.get("recommended_take_profit"),
                "position_size": geometry.get("position_size"),
                "risk_reward": geometry.get("risk_reward"),
                "warnings": market_state.get("warnings") or [],
                "volatility": market_state.get("volatility"),
                "session": market_state.get("sessions"),
                "news_risk": market_state.get("news_risk"),
                "entry": geometry.get("entry"),
                "bias": geometry.get("bias"),
                "atr": geometry.get("atr"),
                "slippage": geometry.get("slippage"),
                "max_drawdown_risk_percent": geometry.get("max_drawdown_risk_percent"),
                "technical_score": technical.get("score"),
                "smc_score": smc.get("score"),
                "source_event_ids": {
                    "technical": technical.get("source_event_id"),
                    "smc": smc.get("source_event_id"),
                },
            }

        assessment = await asyncio.to_thread(_compute)
        self._mark_published(key)
        self._buffer.pop(key, None)
        self._assessments += 1

        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "agent=%s action=assess status=ok symbol=%s risk_score=%s "
            "duration_ms=%.2f warnings=%s",
            self.id,
            symbol,
            assessment["risk_score"],
            duration_ms,
            assessment["warnings"],
        )

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.RISK_ASSESSMENT_COMPLETED,
            source=self.id,
            payload=assessment,
            correlation_id=slot.get("correlation_id"),
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update(
            {
                "assessments_completed": self._assessments,
                "buffer_size": len(self._buffer),
            }
        )
        return base
