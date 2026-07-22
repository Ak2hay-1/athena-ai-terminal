"""Tests for cursor-based historical candle loading."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock

from app.repositories.market_repository import MarketRepository


def test_get_latest_candles_applies_before_filter() -> None:
    db = MagicMock()
    repo = MarketRepository(db)

    before = datetime(2024, 6, 1, tzinfo=timezone.utc)
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    db.scalars.return_value = scalars_result

    result = repo.get_latest_candles(
        "XAUUSD",
        "M5",
        limit=100,
        before=before,
    )

    assert result == []
    stmt = db.scalars.call_args.args[0]
    compiled = str(stmt)
    assert "market_candles.time <" in compiled.lower() or "time <" in compiled.lower()


def test_get_latest_candles_without_before_omits_cursor() -> None:
    db = MagicMock()
    repo = MarketRepository(db)

    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    db.scalars.return_value = scalars_result

    repo.get_latest_candles("XAUUSD", "M5", limit=50)

    stmt = db.scalars.call_args.args[0]
    compiled = str(stmt).lower()
    assert "time <" not in compiled
