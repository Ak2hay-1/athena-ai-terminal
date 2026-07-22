"""OutcomeTracker path detection tests."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.learning.outcome_tracker import OutcomeTracker


def test_buy_tp_hit():
    candles = [
        SimpleNamespace(high=3381, low=3355, close=3375),
    ]
    result, exit_price, bars = OutcomeTracker._detect_path(
        signal="BUY",
        entry=3360,
        sl=3350,
        tp=3380,
        candles=candles,
    )
    assert result == "TP_HIT"
    assert exit_price == 3380
    assert bars == 1


def test_buy_sl_before_tp_same_bar():
    candles = [
        SimpleNamespace(high=3385, low=3345, close=3360),
    ]
    result, exit_price, bars = OutcomeTracker._detect_path(
        signal="BUY",
        entry=3360,
        sl=3350,
        tp=3380,
        candles=candles,
    )
    assert result == "SL_HIT"
    assert exit_price == 3350


def test_timeout_uses_last_close():
    candles = [
        SimpleNamespace(high=3365, low=3355, close=3362),
        SimpleNamespace(high=3368, low=3358, close=3364),
    ]
    result, exit_price, bars = OutcomeTracker._detect_path(
        signal="BUY",
        entry=3360,
        sl=3350,
        tp=3380,
        candles=candles,
    )
    assert result == "TIMEOUT"
    assert exit_price == 3364
    assert bars == 2


def test_entry_price_prefers_entry_price_field():
    rec = SimpleNamespace(entry_price=3360.5, entry=None)
    candle = SimpleNamespace(close=1.0)
    assert OutcomeTracker._entry_price(rec, candle) == 3360.5


def test_label_from_result():
    assert OutcomeTracker._label_from_result("TP_HIT", 1, 2, "BUY") == "WIN"
    assert OutcomeTracker._label_from_result("SL_HIT", 1, 2, "BUY") == "LOSS"
    assert OutcomeTracker._label_from_result("TIMEOUT", 10, 12, "BUY") == "WIN"
