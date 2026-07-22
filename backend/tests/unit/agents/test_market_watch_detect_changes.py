"""Unit tests for Market Watch detect_changes + scanner state cache."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.agents.market_watch.scanner import PairState
from app.agents.market_watch.scanner import detect_changes
from app.services.scanner_state import ScannerStateStore


def _make_candles(
    n: int = 60,
    *,
    start: float = 1.1000,
    step: float = 0.0001,
    volume: float = 100.0,
    volume_last: float | None = None,
) -> list[dict]:
    base = datetime(2024, 6, 3, 12, 0, tzinfo=timezone.utc)
    candles: list[dict] = []
    price = start
    for i in range(n):
        o = price
        c = price + step
        h = max(o, c) + abs(step)
        low = min(o, c) - abs(step)
        vol = volume_last if (i == n - 1 and volume_last is not None) else volume
        candles.append(
            {
                "time": (base + timedelta(minutes=i)).isoformat(),
                "open": o,
                "high": h,
                "low": low,
                "close": c,
                "tick_volume": vol,
            }
        )
        price = c
    return candles


def test_detect_changes_requires_min_candles() -> None:
    state = PairState()
    assert detect_changes(
        symbol="EURUSD",
        timeframe="M5",
        candles=_make_candles(10),
        state=state,
    ) == []


def test_detect_changes_emits_new_candle() -> None:
    state = PairState()
    candles = _make_candles(60)
    changes = detect_changes(
        symbol="EURUSD",
        timeframe="M5",
        candles=candles,
        state=state,
    )
    types = {c["change_type"] for c in changes}
    assert "new_candle" in types
    assert state.last_candle_time is not None


def test_detect_changes_volume_spike() -> None:
    state = PairState()
    candles = _make_candles(60, volume=100.0, volume_last=500.0)
    # Prime state so we still get volume_spike on same candle time if re-run
    first = detect_changes(
        symbol="EURUSD",
        timeframe="M5",
        candles=candles,
        state=state,
    )
    types = {c["change_type"] for c in first}
    assert "volume_spike" in types


def test_detect_changes_breakout_vs_prior_resistance() -> None:
    candles = _make_candles(60, start=1.10, step=0.0002)
    state = PairState(
        last_candle_time=candles[-1]["time"],
        resistance=1.10,
        support=1.05,
        trend_alignment="bullish",
    )
    changes = detect_changes(
        symbol="EURUSD",
        timeframe="M5",
        candles=candles,
        state=state,
    )
    types = {c["change_type"] for c in changes}
    assert "breakout" in types


def test_scanner_state_records_urgent_events_and_meta() -> None:
    store = ScannerStateStore()
    now = datetime.now(timezone.utc)
    event = store.record_market_watch(
        symbol="xauusd",
        timeframe="m15",
        change_type="breakout",
        price=2400.0,
        at=now,
    )
    assert event is not None
    assert event.weight >= 10.0

    got = store.get_event("XAUUSD", "M15", max_age_seconds=300)
    assert got is not None
    assert got.change_type == "breakout"

    ignored = store.record_market_watch(
        symbol="XAUUSD",
        timeframe="M15",
        change_type="new_candle",
        at=now,
    )
    assert ignored is None

    store.mark_scan(at=now, universe_size=24)
    meta = store.snapshot_meta()
    assert meta["universe_size"] == 24
    assert meta["last_market_watch_scan_at"] == now
