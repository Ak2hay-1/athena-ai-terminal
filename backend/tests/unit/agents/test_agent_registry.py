"""Unit tests for AgentRegistry."""

from __future__ import annotations

import pytest

from app.agents._stub import StubAgent
from app.agents.registry import AgentRegistry
from app.events.base import Event


class _AlphaAgent(StubAgent):
    id = "alpha"
    name = "Alpha"
    priority = 5


class _BetaAgent(StubAgent):
    id = "beta"
    name = "Beta"
    priority = 15


def test_register_find_list_enable_disable() -> None:
    registry = AgentRegistry()
    alpha = _AlphaAgent()
    beta = _BetaAgent()

    registry.register(alpha)
    registry.register(beta)

    assert registry.find("alpha") is alpha
    assert [a.id for a in registry.list()] == ["alpha", "beta"]

    assert registry.disable("alpha") is True
    assert alpha.enabled is False
    assert [a.id for a in registry.list(enabled_only=True)] == ["beta"]

    assert registry.enable("alpha") is True
    assert alpha.enabled is True

    registry.unregister("beta")
    assert registry.find("beta") is None


def test_discover_stub_agents() -> None:
    registry = AgentRegistry()
    classes = registry.discover("app.agents")
    ids = {cls.id for cls in classes}

    assert "market_watch" in ids
    assert "technical" in ids
    assert "smc" in ids
    assert "risk" in ids
    assert "validation" in ids
    assert "learning" in ids
    assert "communication" in ids
    assert "portfolio" in ids
    assert "watchlist" in ids
    assert "news" in ids
    assert "memory" in ids
    assert "reasoning" in ids
    assert len(classes) >= 12


def test_instantiate_discovered_registers_instances() -> None:
    registry = AgentRegistry()
    instances = registry.instantiate_discovered("app.agents")
    assert len(instances) >= 9
    assert registry.find("market_watch") is not None


@pytest.mark.asyncio
async def test_stub_handle_event() -> None:
    agent = _AlphaAgent()
    await agent.initialize()
    event = Event(type="SystemTick", source="test")
    await agent.process_event(event)
    health = agent.health()
    assert health["status"] == "running"
    assert agent.metrics()["events_processed"] == 1
    await agent.shutdown()
