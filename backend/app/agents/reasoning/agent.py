"""
Reasoning Agent — runs after high-quality TradeValidationCompleted only.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.memory.retrieval import MemoryRetrieval
from app.ai.reasoning import setup_reasoning_engine
from app.ai.reasoning import should_run_reasoning
from app.core.logger import get_logger
from app.core.settings import settings
from app.events.base import Event
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.memory.service import MemoryService

logger = get_logger("athena.agents.reasoning")


class ReasoningAgent(BaseAgent):
    id = "reasoning"
    name = "Reasoning Agent"
    version = "1.0.0"
    priority = 70
    subscribed_events = [EventType.TRADE_VALIDATION_COMPLETED]

    def __init__(self) -> None:
        super().__init__()
        self._retrieval = MemoryRetrieval(MemoryService())
        self._runs = 0
        self._skipped = 0

    async def handle_event(self, event: Event) -> None:
        if not settings.REASONING_ENABLED:
            return
        if str(event.type) != EventType.TRADE_VALIDATION_COMPLETED:
            return

        payload = dict(event.payload or {})
        if not should_run_reasoning(payload):
            self._skipped += 1
            logger.info(
                "agent=%s action=skip status=%s confluence=%s",
                self.id,
                payload.get("status"),
                payload.get("confluence"),
            )
            return

        similar = self._retrieval.similar_setups(
            payload,
            top_k=int(settings.REASONING_SIMILAR_TRADES_TOP_K),
        )

        evidence = {
            "symbol": payload.get("symbol"),
            "timeframe": payload.get("timeframe"),
            "candle_time": payload.get("candle_time"),
            "status": payload.get("status"),
            "confluence": payload.get("confluence"),
            "validation_score": payload.get("validation_score"),
            "approval": payload.get("approval"),
            "reasons": payload.get("reasons"),
            "scores": payload.get("scores"),
        }

        result = await setup_reasoning_engine.reason(evidence, similar)
        self._runs += 1

        out_payload = {
            "symbol": evidence.get("symbol"),
            "timeframe": evidence.get("timeframe"),
            "candle_time": evidence.get("candle_time"),
            "summary": result.summary,
            "institutional_reasoning": result.institutional_reasoning,
            "potential_risks": result.potential_risks,
            "alternative_scenarios": result.alternative_scenarios,
            "confidence_explanation": result.confidence_explanation,
            "what_to_watch": result.what_to_watch,
            "evidence_citations": result.evidence_citations,
            "similar_trades": {
                "count": similar.get("count"),
                "win_rate": similar.get("win_rate"),
                "average_rr": similar.get("average_rr"),
                "average_duration_minutes": similar.get(
                    "average_duration_minutes"
                ),
            },
            "provider": result.provider,
            "model": result.model,
            "success": result.success,
            "message": result.message,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "latency_ms": result.latency_ms,
            "cost_usd": result.cost_usd,
            "scores": payload.get("scores"),
            "confluence": payload.get("confluence"),
            "status": payload.get("status"),
        }

        publisher = self._publisher or EventPublisher()
        await publisher.publish(
            EventType.REASONING_COMPLETED,
            source=self.id,
            payload=out_payload,
            correlation_id=event.correlation_id or event.id,
        )
        logger.info(
            "agent=%s action=reason status=%s symbol=%s success=%s",
            self.id,
            payload.get("status"),
            payload.get("symbol"),
            result.success,
        )

    def health(self) -> dict[str, Any]:
        base = super().health()
        base.update(
            {
                "reasoning_runs": self._runs,
                "reasoning_skipped": self._skipped,
            }
        )
        return base
