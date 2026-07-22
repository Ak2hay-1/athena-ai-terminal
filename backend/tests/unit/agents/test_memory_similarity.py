"""Unit tests for memory similarity search."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from app.agents.memory.embeddings import build_feature_vector
from app.agents.memory.embeddings import cosine_similarity
from app.agents.memory.retrieval import MemoryRetrieval


class _FakeMemoryService:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def query(self, **kwargs: Any) -> list[Any]:
        rows = self.rows
        if kwargs.get("memory_type"):
            rows = [r for r in rows if r.memory_type == kwargs["memory_type"]]
        if kwargs.get("symbol"):
            rows = [r for r in rows if r.symbol == kwargs.get("symbol")]
        return rows


def _row(payload: dict, memory_type: str = "trade_outcome") -> Any:
    return SimpleNamespace(
        id=payload.get("id", 1),
        agent_id="trade",
        memory_type=memory_type,
        payload=payload,
        symbol=payload.get("symbol"),
        timeframe=payload.get("timeframe"),
        correlation_id=None,
        created_at=None,
    )


def test_cosine_identity() -> None:
    vec = build_feature_vector(
        {"scores": {"technical": 80, "smc": 80, "risk": 80}, "confluence": 80}
    )
    assert cosine_similarity(vec, vec) == 1.0


def test_similar_setups_ranks_and_aggregates() -> None:
    current = {
        "symbol": "EURUSD",
        "timeframe": "M5",
        "status": "APPROVED",
        "confluence": 85,
        "scores": {"technical": 84, "smc": 86, "risk": 88, "risk_reward": 2.3},
    }
    rows = [
        _row(
            {
                "id": 1,
                "symbol": "EURUSD",
                "timeframe": "M5",
                "status": "APPROVED",
                "confluence": 84,
                "scores": {"technical": 83, "smc": 85, "risk": 87, "risk_reward": 2.2},
                "outcome": "win",
                "duration_minutes": 30,
            }
        ),
        _row(
            {
                "id": 2,
                "symbol": "EURUSD",
                "timeframe": "M5",
                "status": "APPROVED",
                "confluence": 82,
                "scores": {"technical": 81, "smc": 83, "risk": 85, "risk_reward": 2.4},
                "outcome": "win",
                "duration_minutes": 40,
            }
        ),
        _row(
            {
                "id": 3,
                "symbol": "EURUSD",
                "timeframe": "M5",
                "status": "REJECTED",
                "confluence": 40,
                "scores": {"technical": 40, "smc": 40, "risk": 40, "risk_reward": 1.0},
                "outcome": "loss",
                "duration_minutes": 10,
            }
        ),
    ]
    retrieval = MemoryRetrieval(_FakeMemoryService(rows))  # type: ignore[arg-type]
    result = retrieval.similar_setups(current, top_k=2)
    assert result["count"] == 2
    assert result["win_rate"] == 100.0
    assert result["average_rr"] > 0
    assert result["items"][0]["similarity"] >= result["items"][1]["similarity"]
