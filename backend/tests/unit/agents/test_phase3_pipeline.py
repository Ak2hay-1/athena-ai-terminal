"""Event pipeline: Technical → SMC → Risk → Validation."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from app.agents.risk.agent import RiskAgent
from app.agents.smc.agent import SmcAgent
from app.agents.validation.agent import ValidationAgent
from app.events.base import Event
from app.events.bus import AsyncEventBus
from app.events.publisher import EventPublisher
from app.events.types import EventType
from app.tools.manager import ToolManager


def _candles(n: int = 100) -> list[dict[str, Any]]:
    rng = np.random.default_rng(21)
    start = datetime(2024, 6, 3, 12, tzinfo=timezone.utc)  # weekday
    close = 1.10 + np.cumsum(rng.normal(0, 0.0003, size=n))
    out = []
    for i in range(n):
        c = float(close[i])
        out.append(
            {
                "time": (start + timedelta(minutes=5 * i)).isoformat(),
                "open": c - 0.0001,
                "high": c + 0.0003,
                "low": c - 0.0003,
                "close": c,
                "tick_volume": int(180 + rng.integers(0, 50)),
                "spread": 10,
            }
        )
    return out


class _FakeMarketDataTool:
    id = "market_data"
    name = "Fake Market Data"

    def __init__(self, candles: list[dict[str, Any]]) -> None:
        self._candles = candles

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        action = kwargs.get("action")
        if action == "get_latest":
            return {
                "status": "ok",
                "candle": self._candles[-1],
            }
        return {
            "status": "ok",
            "candles": self._candles,
            "count": len(self._candles),
        }

    def health(self) -> dict[str, Any]:
        return {"id": self.id, "status": "ready"}


@pytest.mark.asyncio
async def test_phase3_event_chain() -> None:
    bus = AsyncEventBus()
    publisher = EventPublisher(bus)
    candles = _candles(120)
    tools = ToolManager()
    tools.register(_FakeMarketDataTool(candles))  # type: ignore[arg-type]

    smc = SmcAgent()
    risk = RiskAgent()
    validation = ValidationAgent()
    for agent in (smc, risk, validation):
        agent.bind_tools(tools)
        agent.bind_publisher(publisher)
        await agent.initialize()

    completed: dict[str, list[Event]] = {
        "smc": [],
        "risk": [],
        "validation": [],
    }

    async def on_smc(event: Event) -> None:
        completed["smc"].append(event)
        await risk.process_event(event)
        await validation.process_event(event)

    async def on_risk(event: Event) -> None:
        completed["risk"].append(event)
        await validation.process_event(event)

    async def on_validation(event: Event) -> None:
        completed["validation"].append(event)

    bus.subscribe(EventType.SMC_ANALYSIS_COMPLETED, on_smc)
    bus.subscribe(EventType.RISK_ASSESSMENT_COMPLETED, on_risk)
    bus.subscribe(EventType.TRADE_VALIDATION_COMPLETED, on_validation)

    candle_time = candles[-1]["time"]
    tech_event = Event(
        type=EventType.TECHNICAL_ANALYSIS_COMPLETED,
        source="technical",
        payload={
            "symbol": "EURUSD",
            "timeframe": "M5",
            "score": 84.0,
            "trend": "Bullish",
            "ema_alignment": "Bullish",
            "candle_time": candle_time,
            "strength": 70,
        },
        correlation_id="EURUSD:M5:phase3",
    )

    with patch(
        "app.agents.risk.agent._fetch_news_context",
        return_value={"high_impact_upcoming": False, "score": 0},
    ):
        # Buffer technical first so Risk/Validation are ready when SMC publishes
        await risk.process_event(tech_event)
        await validation.process_event(tech_event)
        await smc.process_event(tech_event)

    assert len(completed["smc"]) == 1
    assert completed["smc"][0].payload["score"] >= 0
    assert "bos" in completed["smc"][0].payload

    assert len(completed["risk"]) == 1
    risk_payload = completed["risk"][0].payload
    assert "risk_score" in risk_payload
    assert "recommended_stop_loss" in risk_payload
    assert "warnings" in risk_payload

    assert len(completed["validation"]) == 1
    val = completed["validation"][0].payload
    assert val["status"] in {"APPROVED", "REJECTED", "WAIT"}
    assert "confluence" in val
    assert "reasons" in val
    assert isinstance(val["approval"], bool)
