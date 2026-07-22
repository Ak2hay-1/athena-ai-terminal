"""Unit tests for AsyncEventBus."""

from __future__ import annotations

import pytest

from app.events.base import Event
from app.events.bus import AsyncEventBus
from app.events.types import EventType


@pytest.mark.asyncio
async def test_publish_subscribe_and_history() -> None:
    bus = AsyncEventBus(history_size=10)
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(EventType.MARKET_UPDATED, handler)
    event = Event(
        type=EventType.MARKET_UPDATED,
        source="test",
        payload={"symbol": "XAUUSD"},
    )
    results = await bus.publish(event)

    assert len(results) == 1
    assert len(received) == 1
    assert received[0].id == event.id
    assert bus.history(limit=5)[-1].id == event.id


@pytest.mark.asyncio
async def test_unsubscribe() -> None:
    bus = AsyncEventBus()
    calls = {"n": 0}

    async def handler(event: Event) -> None:
        calls["n"] += 1

    bus.subscribe(EventType.NEWS_RECEIVED, handler)
    bus.unsubscribe(EventType.NEWS_RECEIVED, handler)
    await bus.publish(
        Event(type=EventType.NEWS_RECEIVED, source="test"),
    )
    assert calls["n"] == 0


@pytest.mark.asyncio
async def test_broadcast_reaches_all_handlers() -> None:
    bus = AsyncEventBus()
    seen: list[str] = []

    async def h1(event: Event) -> None:
        seen.append("h1")

    async def h2(event: Event) -> None:
        seen.append("h2")

    bus.subscribe(EventType.TRADE_CREATED, h1)
    bus.subscribe(EventType.TRADE_CLOSED, h2)

    await bus.broadcast(Event(type=EventType.SYSTEM_TICK, source="test"))
    assert set(seen) == {"h1", "h2"}


@pytest.mark.asyncio
async def test_handler_error_isolation() -> None:
    bus = AsyncEventBus()
    ok_calls = {"n": 0}

    async def bad(event: Event) -> None:
        raise RuntimeError("boom")

    async def good(event: Event) -> None:
        ok_calls["n"] += 1

    bus.subscribe(EventType.RISK_CHANGED, bad)
    bus.subscribe(EventType.RISK_CHANGED, good)

    results = await bus.publish(
        Event(type=EventType.RISK_CHANGED, source="test"),
    )

    assert ok_calls["n"] == 1
    assert any(isinstance(r, Exception) for r in results)
    assert bus.metrics()["dispatch_failures"] >= 1
