"""Unit tests for Athena multi-layer CacheManager."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import pytest

from app.cache.ai_context_cache import AiContextCache
from app.cache.indicator_cache import IndicatorCache
from app.cache.ram_cache import RamCache
from app.cache.types import candle_to_tuple
from app.cache.types import model_to_tuple
from app.cache.types import tuple_to_dict


def _bar(epoch: int, close: float = 1.0):
    return candle_to_tuple(
        time=epoch,
        open_=close,
        high=close + 0.1,
        low=close - 0.1,
        close=close,
        tick_volume=10,
    )


def test_ram_cache_lru_and_limit() -> None:
    ram = RamCache(max_candles_per_series=5, max_series=2, max_memory_mb=64)
    bars = [_bar(1_700_000_000 + i * 60, float(i)) for i in range(10)]
    ram.put_candles("EURUSD", "M5", bars, replace=True)

    got = ram.get_candles("EURUSD", "M5")
    assert got is not None
    assert len(got) == 5
    assert got[0][0] == bars[-5][0]

    ram.put_candles("GBPUSD", "M5", bars[:3], replace=True)
    ram.put_candles("USDJPY", "M5", bars[:3], replace=True)
    # max_series=2 → oldest series evicted
    assert ram.get_candles("EURUSD", "M5") is None
    assert ram.get_candles("USDJPY", "M5") is not None


def test_ram_append_closed_candle_replaces_same_bucket() -> None:
    ram = RamCache()
    ram.put_candles("XAUUSD", "M1", [_bar(1_700_000_000, 2000.0)])
    ram.append_closed_candle(
        "XAUUSD", "M1", _bar(1_700_000_000, 2001.0)
    )
    series = ram.get_candles("XAUUSD", "M1")
    assert series is not None
    assert len(series) == 1
    assert series[0][4] == 2001.0

    ram.append_closed_candle(
        "XAUUSD", "M1", _bar(1_700_000_060, 2002.0)
    )
    series = ram.get_candles("XAUUSD", "M1")
    assert series is not None
    assert len(series) == 2


def test_inactive_cleanup() -> None:
    ram = RamCache(inactive_ttl_seconds=60)
    ram.put_candles("EURUSD", "M5", [_bar(1_700_000_000)])
    entry = ram._series[ram.series_key("EURUSD", "M5")]
    entry.last_access = entry.last_access - 120
    removed = ram.cleanup_inactive()
    assert removed == 1
    assert ram.get_candles("EURUSD", "M5") is None


def test_indicator_cache_hit_on_same_fingerprint() -> None:
    ram = RamCache()
    cache = IndicatorCache(ram, enabled=True)
    candles = [_bar(1_700_000_000 + i * 60, float(i)) for i in range(50)]
    calls = {"n": 0}

    def compute(_candles):
        calls["n"] += 1
        return {"rsi": 55.0}

    a = cache.get_or_compute("EURUSD", "M5", candles, compute)
    b = cache.get_or_compute("EURUSD", "M5", candles, compute)
    assert a == b == {"rsi": 55.0}
    assert calls["n"] == 1

    # New candle → miss
    candles2 = candles + [_bar(1_700_000_000 + 50 * 60, 50.0)]
    cache.get_or_compute("EURUSD", "M5", candles2, compute)
    assert calls["n"] == 2


def test_ai_context_ttl_and_candle_invalidation() -> None:
    ai = AiContextCache(ttl_seconds=30)
    ai.set("EURUSD", "M5", {"trend": "up"}, candle_epoch=100)
    assert ai.get("EURUSD", "M5")["trend"] == "up"

    ai.invalidate_on_candle("EURUSD", "M5", candle_epoch=200)
    assert ai.get("EURUSD", "M5") is None


def test_tuple_roundtrip() -> None:
    raw = {
        "time": datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        "open": 1.1,
        "high": 1.2,
        "low": 1.0,
        "close": 1.15,
        "tick_volume": 42,
        "spread": 1,
        "real_volume": 0,
    }
    bar = model_to_tuple(raw)
    payload = tuple_to_dict(bar, symbol="EURUSD", timeframe="M5")
    assert payload["symbol"] == "EURUSD"
    assert payload["close"] == 1.15
    assert "2024-01-01" in payload["time"]


def test_cache_manager_get_candles_ram_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.cache.manager import CacheManager

    mgr = CacheManager()
    bars = [_bar(1_700_000_000 + i * 300, float(i)) for i in range(20)]
    mgr.ram.put_candles("EURUSD", "M5", bars, replace=True)

    # Avoid DB / preload side effects
    monkeypatch.setattr(mgr, "_load_from_db", lambda *a, **k: [])
    monkeypatch.setattr(mgr.preloader, "on_chart_open", lambda *a, **k: None)

    result = mgr.get_candles("EURUSD", "M5", limit=10, sync_if_stale=False)
    assert len(result) == 10
    assert result[-1]["close"] == 19.0
    snap = mgr.metrics.snapshot()
    assert snap["ram_hits"] >= 1


def test_invalidate_clears_series() -> None:
    from app.cache.manager import CacheManager

    mgr = CacheManager()
    mgr.ram.put_candles("EURUSD", "M5", [_bar(1_700_000_000)])
    mgr.ai.set("EURUSD", "M5", {"trend": "up"})
    mgr.invalidate("EURUSD", "M5", reason="test")
    assert mgr.ram.get_candles("EURUSD", "M5") is None
    assert mgr.ai.get("EURUSD", "M5") is None
