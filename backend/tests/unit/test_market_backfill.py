"""Tests for MT5 → DB candle backfill."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

from app.schemas.market import MarketBackfillResult
from app.services.market_service import MarketService


def test_backfill_candles_caps_count_and_returns_stats() -> None:
    db = MagicMock()
    service = MarketService(db)

    stats = {
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "candle_count": 12000,
        "first_candle": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "last_candle": datetime(2024, 6, 1, tzinfo=timezone.utc),
    }
    service.market.get_statistics = MagicMock(return_value=stats)

    with (
        patch("app.core.settings.settings") as mock_settings,
        patch("app.mt5.candle_collector.CandleCollector") as mock_collector_cls,
        patch("app.mt5.client.mt5_client") as mock_mt5,
    ):
        mock_mt5.initialize.return_value = True
        mock_settings.MARKET_BACKFILL_BARS = 100000
        mock_settings.MARKET_COLLECTOR_BARS = 50000
        collector = MagicMock()
        collector.collect.return_value = 42
        mock_collector_cls.return_value = collector

        result = service.backfill_candles("xauusd", "m5", count=999999)

    assert isinstance(result, MarketBackfillResult)
    assert result.symbol == "XAUUSD"
    assert result.timeframe == "M5"
    assert result.requested == 100000
    assert result.inserted == 42
    assert result.candle_count == 12000
    assert result.oldest == stats["first_candle"]
    assert result.newest == stats["last_candle"]
    collector.collect.assert_called_once_with("XAUUSD", "M5", count=50000)


def test_backfill_candles_raises_when_mt5_disconnected() -> None:
    from app.core.exceptions import MT5Exception

    db = MagicMock()
    service = MarketService(db)

    with patch("app.mt5.client.mt5_client") as mock_mt5:
        mock_mt5.initialize.return_value = False
        try:
            service.backfill_candles("GBPUSD", "M5", count=10)
            raised = False
        except MT5Exception as exc:
            raised = True
            assert "not connected" in exc.message.lower()

    assert raised


def test_backfill_candles_raises_when_mt5_returns_no_bars() -> None:
    from app.core.exceptions import MT5Exception

    db = MagicMock()
    service = MarketService(db)
    service.market.get_statistics = MagicMock(
        return_value={
            "symbol": "GBPUSD",
            "timeframe": "M5",
            "candle_count": 0,
            "first_candle": None,
            "last_candle": None,
        }
    )

    with (
        patch("app.core.settings.settings") as mock_settings,
        patch("app.mt5.candle_collector.CandleCollector") as mock_collector_cls,
        patch("app.mt5.client.mt5_client") as mock_mt5,
    ):
        mock_mt5.initialize.return_value = True
        mock_settings.MARKET_BACKFILL_BARS = 1000
        mock_settings.MARKET_COLLECTOR_BARS = 500
        collector = MagicMock()
        collector.collect.return_value = 0
        mock_collector_cls.return_value = collector

        try:
            service.backfill_candles("GBPUSD", "M5", count=10)
            raised = False
        except MT5Exception as exc:
            raised = True
            assert "No candle data" in exc.message

    assert raised


def test_maybe_startup_backfill_skips_when_above_threshold() -> None:
    db = MagicMock()
    service = MarketService(db)
    service.market.get_statistics = MagicMock(
        return_value={
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "candle_count": 9000,
            "first_candle": None,
            "last_candle": None,
        }
    )

    with patch("app.core.settings.settings") as mock_settings:
        mock_settings.MARKET_STARTUP_BACKFILL_ENABLED = True
        mock_settings.MARKET_STARTUP_BACKFILL_THRESHOLD = 5000
        result = service.maybe_startup_backfill("XAUUSD", "M5")

    assert result is None
