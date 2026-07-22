"""
Normalize agent evidence into MemoryService rows.
"""

from __future__ import annotations

from typing import Any

from app.agents.memory.embeddings import build_feature_vector
from app.memory.service import MemoryService
from app.models.agent_memory import AgentMemory


class MemoryStorage:
    """Persist structured market intelligence (not chat)."""

    def __init__(self, memory: MemoryService | None = None) -> None:
        self._memory = memory or MemoryService()

    def store_evidence(
        self,
        *,
        agent_id: str,
        memory_type: str,
        payload: dict[str, Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        correlation_id: str | None = None,
        source_event: str | None = None,
    ) -> AgentMemory:
        enriched = dict(payload)
        enriched["feature_vector"] = build_feature_vector(enriched)
        meta = {"source_event": source_event} if source_event else None
        return self._memory.store(
            agent_id=agent_id,
            memory_type=memory_type,
            payload=enriched,
            symbol=symbol,
            timeframe=timeframe,
            correlation_id=correlation_id,
            meta=meta,
        )

    def store_from_event_type(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> AgentMemory | None:
        symbol = str(payload.get("symbol") or "").upper() or None
        timeframe = str(payload.get("timeframe") or "").upper() or None
        mapping: dict[str, tuple[str, str]] = {
            "TechnicalAnalysisCompleted": ("observation", "technical"),
            "SMCAnalysisCompleted": ("observation", "smc"),
            "RiskAssessmentCompleted": ("observation", "risk"),
            "TradeValidationCompleted": ("decision", "validation"),
            "NewsAnalysisCompleted": ("observation", "news"),
            "ReasoningCompleted": ("reasoning", "reasoning"),
            "TradeClosed": ("trade_outcome", "trade"),
            "LearningCompleted": ("statistic", "learning"),
            "PortfolioUpdated": ("statistic", "portfolio"),
            "WatchlistOpportunityDetected": ("observation", "watchlist"),
            "NotificationDispatched": ("observation", "communication"),
        }
        if event_type not in mapping:
            return None
        memory_type, agent_id = mapping[event_type]
        return self.store_evidence(
            agent_id=agent_id,
            memory_type=memory_type,
            payload=payload,
            symbol=symbol,
            timeframe=timeframe,
            correlation_id=correlation_id,
            source_event=event_type,
        )
