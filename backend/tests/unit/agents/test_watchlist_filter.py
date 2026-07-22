"""Unit tests for watchlist filtering and opportunity detection."""

from __future__ import annotations

from app.agents.watchlist.detector import is_opportunity
from app.agents.watchlist.filter import matches_watchlist
from app.agents.watchlist.preferences import UserWatchContext
from app.core.settings import settings


def test_filter_favorites_ignored_and_session() -> None:
    ctx = UserWatchContext(
        user_id=1,
        symbols={"EURUSD", "XAUUSD"},
        symbol_timeframes={("EURUSD", "M5"), ("XAUUSD", "H1")},
        ignored_symbols={"XAUUSD"},
        preferred_sessions={"london"},
        preferred_timeframes=set(),
    )
    assert matches_watchlist(ctx, symbol="EURUSD", timeframe="M5", session="london")
    assert not matches_watchlist(ctx, symbol="XAUUSD", timeframe="H1", session="london")
    assert not matches_watchlist(ctx, symbol="GBPUSD", timeframe="M5", session="london")
    assert not matches_watchlist(ctx, symbol="EURUSD", timeframe="M5", session="asia")


def test_opportunity_gate() -> None:
    original = settings.WATCHLIST_MIN_CONFLUENCE
    try:
        object.__setattr__(settings, "WATCHLIST_MIN_CONFLUENCE", 75.0)
    except Exception:
        pass
    assert is_opportunity(
        {"status": "APPROVED", "confluence": 80},
        event_type="TradeValidationCompleted",
    )
    assert not is_opportunity(
        {"status": "REJECTED", "confluence": 90},
        event_type="TradeValidationCompleted",
    )
    assert not is_opportunity(
        {"status": "APPROVED", "confluence": 50},
        event_type="TradeValidationCompleted",
    )
    assert is_opportunity(
        {"score": 80},
        event_type="TechnicalAnalysisCompleted",
    )
    _ = original
