"""Integration-style unit test: MarketUpdated → Technical → TechnicalAnalysisCompleted."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import numpy as np
import pytest

from app.agents.technical.agent import TechnicalAgent
from app.events.base import Event
from app.events.bus import AsyncEventBus
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.tools.manager import ToolManager


def _make_candles(n: int = 100) -> list[dict[str, Any]]:
    rng = np.random.default_rng(7)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    close = 1.10 + np.cumsum(rng.normal(0, 0.0005, size=n))
    candles = []
    for i in range(n):
        c = float(close[i])
        candles.append(
            {
                "time": (start + timedelta(minutes=5 * i)).isoformat(),
                "open": c - 0.0001,
                "high": c + 0.0003,
                "low": c - 0.0003,
                "close": c,
                "tick_volume": int(200 + rng.integers(0, 100)),
            }
        )
    return candles


class _FakeMarketDataTool:
    id = "market_data"
    name = "Fake Market Data"

    def __init__(self, candles: list[dict[str, Any]]) -> None:
        self._candles = candles

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "ok",
            "tool_id": self.id,
            "action": kwargs.get("action"),
            "candles": self._candles,
            "count": len(self._candles),
        }

    def health(self) -> dict[str, Any]:
        return {"id": self.id, "status": "ready"}


@pytest.mark.asyncio
async def test_market_updated_triggers_technical_analysis() -> None:
    bus = AsyncEventBus()
    publisher = EventPublisher(bus)
    completed: list[Event] = []

    async def on_complete(event: Event) -> None:
        completed.append(event)

    bus.subscribe(EventType.TECHNICAL_ANALYSIS_COMPLETED, on_complete)

    candles = _make_candles(120)
    tools = ToolManager()
    tools.register(_FakeMarketDataTool(candles))  # type: ignore[arg-type]

    agent = TechnicalAgent()
    agent.bind_tools(tools)
    agent.bind_publisher(publisher)
    await agent.initialize()

    market_event = Event(
        type=EventType.MARKET_UPDATED,
        source="market_watch",
        payload={
            "symbol": "EURUSD",
            "timeframe": "M5",
            "price": candles[-1]["close"],
            "timestamp": candles[-1]["time"],
            "market_state": {},
            "previous_state": {},
            "reason": "new_candle",
            "change_type": "new_candle",
        },
        correlation_id="EURUSD:M5:test",
    )

    # Simulate manager dispatch
    await agent.process_event(market_event)
    # Allow bus handlers to finish (publish awaits handlers)
    assert len(completed) == 1

    payload = completed[0].payload
    assert payload["symbol"] == "EURUSD"
    assert payload["timeframe"] == "M5"
    assert 0 <= payload["score"] <= 100
    assert "indicators" in payload
    assert "trend" in payload
    assert "strength" in payload
    assert "support" in payload
    assert "resistance" in payload
    assert completed[0].type == EventType.TECHNICAL_ANALYSIS_COMPLETED

    # Same candle should not republish
    await agent.process_event(market_event)
    assert len(completed) == 1
