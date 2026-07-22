"""Unit tests for memory storage and trade replay."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from types import SimpleNamespace
from typing import Any

from app.agents.memory.retrieval import MemoryRetrieval
from app.agents.memory.storage import MemoryStorage


class _FakeMemoryService:
    def __init__(self) -> None:
        self.rows: list[Any] = []
        self._id = 1

    def store(self, **kwargs: Any) -> Any:
        row = SimpleNamespace(
            id=self._id,
            agent_id=kwargs["agent_id"],
            memory_type=kwargs["memory_type"],
            payload=kwargs["payload"],
            symbol=kwargs.get("symbol"),
            timeframe=kwargs.get("timeframe"),
            correlation_id=kwargs.get("correlation_id"),
            created_at=datetime.now(timezone.utc),
            meta=kwargs.get("meta"),
        )
        self._id += 1
        self.rows.append(row)
        return row

    def query(self, **kwargs: Any) -> list[Any]:
        rows = self.rows
        if kwargs.get("memory_type"):
            rows = [r for r in rows if r.memory_type == kwargs["memory_type"]]
        if kwargs.get("correlation_id"):
            rows = [r for r in rows if r.correlation_id == kwargs["correlation_id"]]
        if kwargs.get("symbol"):
            rows = [r for r in rows if r.symbol == kwargs["symbol"]]
        return rows[: int(kwargs.get("limit") or 50)]


def test_store_and_replay_by_correlation_id() -> None:
    service = _FakeMemoryService()
    storage = MemoryStorage(service)  # type: ignore[arg-type]
    retrieval = MemoryRetrieval(service)  # type: ignore[arg-type]

    storage.store_from_event_type(
        "TechnicalAnalysisCompleted",
        {"symbol": "EURUSD", "timeframe": "M5", "score": 80},
        correlation_id="corr-1",
    )
    storage.store_from_event_type(
        "TradeValidationCompleted",
        {
            "symbol": "EURUSD",
            "timeframe": "M5",
            "status": "APPROVED",
            "confluence": 85,
            "scores": {"technical": 80, "smc": 82, "risk": 90, "risk_reward": 2.2},
        },
        correlation_id="corr-1",
    )

    replay = retrieval.trade_replay("corr-1")
    assert len(replay) == 2
    assert replay[0]["memory_type"] == "observation"
    assert replay[1]["memory_type"] == "decision"
    assert "feature_vector" in replay[0]["payload"]
