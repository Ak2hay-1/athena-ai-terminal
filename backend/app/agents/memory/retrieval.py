"""
Memory retrieval, trade replay, and similarity search.
"""

from __future__ import annotations

from typing import Any

from app.agents.memory.embeddings import build_feature_vector
from app.agents.memory.embeddings import cosine_similarity
from app.agents.memory.embeddings import vector_from_memory_payload
from app.core.settings import settings
from app.memory.service import MemoryService
from app.models.agent_memory import AgentMemory


class MemoryRetrieval:
    """Query and similarity search over trading intelligence memory."""

    def __init__(self, memory: MemoryService | None = None) -> None:
        self._memory = memory or MemoryService()

    def query(
        self,
        *,
        agent_id: str | None = None,
        memory_type: str | None = None,
        symbol: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentMemory]:
        return self._memory.query(
            agent_id=agent_id,
            memory_type=memory_type,
            symbol=symbol,
            correlation_id=correlation_id,
            limit=limit,
        )

    def trade_replay(self, correlation_id: str) -> list[dict[str, Any]]:
        rows = self.query(correlation_id=correlation_id, limit=100)
        # Oldest first for replay
        ordered = sorted(rows, key=lambda r: r.created_at or r.id)
        return [
            {
                "id": row.id,
                "agent_id": row.agent_id,
                "memory_type": row.memory_type,
                "symbol": row.symbol,
                "timeframe": row.timeframe,
                "payload": row.payload,
                "created_at": (
                    row.created_at.isoformat() if row.created_at else None
                ),
            }
            for row in ordered
        ]

    def similar_setups(
        self,
        setup: dict[str, Any],
        *,
        top_k: int | None = None,
        memory_types: tuple[str, ...] = ("decision", "trade_outcome"),
    ) -> dict[str, Any]:
        """
        Rank historical setups by feature cosine similarity.
        """
        k = top_k or int(settings.MEMORY_SIMILARITY_TOP_K)
        query_vec = build_feature_vector(setup)
        candidates: list[AgentMemory] = []
        for memory_type in memory_types:
            candidates.extend(
                self.query(
                    memory_type=memory_type,
                    symbol=setup.get("symbol"),
                    limit=200,
                )
            )

        scored: list[tuple[float, AgentMemory]] = []
        for row in candidates:
            payload = row.payload or {}
            vec = vector_from_memory_payload(payload)
            score = cosine_similarity(query_vec, vec)
            scored.append((score, row))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:k]

        wins = 0
        losses = 0
        rr_values: list[float] = []
        durations: list[float] = []
        items: list[dict[str, Any]] = []
        for sim, row in top:
            payload = row.payload or {}
            outcome = str(payload.get("outcome") or payload.get("result") or "").lower()
            if outcome in {"win", "tp", "profit", "success"}:
                wins += 1
            elif outcome in {"loss", "sl", "fail", "failure"}:
                losses += 1
            rr = payload.get("risk_reward") or (payload.get("scores") or {}).get(
                "risk_reward"
            )
            if rr is not None:
                try:
                    rr_values.append(float(rr))
                except (TypeError, ValueError):
                    pass
            duration = payload.get("duration_minutes") or payload.get("duration")
            if duration is not None:
                try:
                    durations.append(float(duration))
                except (TypeError, ValueError):
                    pass
            items.append(
                {
                    "id": row.id,
                    "similarity": round(sim, 4),
                    "symbol": row.symbol,
                    "timeframe": row.timeframe,
                    "memory_type": row.memory_type,
                    "payload": payload,
                }
            )

        sample = wins + losses
        win_rate = (wins / sample * 100.0) if sample else 0.0
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "count": len(items),
            "items": items,
            "win_rate": round(win_rate, 2),
            "average_rr": round(avg_rr, 2),
            "average_duration_minutes": round(avg_duration, 2),
            "wins": wins,
            "losses": losses,
        }
