"""Unit tests for Market Watch duplicate prevention."""

from __future__ import annotations

import pytest

from app.agents.market_watch.publisher import MarketWatchPublisher
from app.events.bus import AsyncEventBus
from app.events.publisher import EventPublisher
from app.events.types import EventType


@pytest.mark.asyncio
async def test_duplicate_change_not_republished() -> None:
    bus = AsyncEventBus()
    received: list = []

    async def handler(event) -> None:
        received.append(event)

    bus.subscribe(EventType.MARKET_UPDATED, handler)
    publisher = MarketWatchPublisher(EventPublisher(bus))

    change = {
        "symbol": "EURUSD",
        "timeframe": "M5",
        "change_type": "new_candle",
        "price": 1.09,
        "timestamp": "2024-01-01T12:00:00+00:00",
        "market_state": {"price": 1.09},
        "previous_state": {},
    }

    assert await publisher.publish_change(change) is True
    assert await publisher.publish_change(change) is False
    assert len(received) == 1
    assert publisher.duplicates_skipped == 1
    assert publisher.events_published == 1


@pytest.mark.asyncio
async def test_new_candle_time_publishes() -> None:
    bus = AsyncEventBus()
    publisher = MarketWatchPublisher(EventPublisher(bus))

    base = {
        "symbol": "EURUSD",
        "timeframe": "M5",
        "change_type": "new_candle",
        "price": 1.09,
        "market_state": {},
        "previous_state": {},
    }
    first = {**base, "timestamp": "2024-01-01T12:00:00+00:00"}
    second = {**base, "timestamp": "2024-01-01T12:05:00+00:00"}

    assert await publisher.publish_change(first) is True
    assert await publisher.publish_change(second) is True
    assert publisher.events_published == 2
