"""Legacy analysis.risk_engine wrapper still rounds symbol-aware levels."""

from __future__ import annotations

from app.analysis.risk_engine import RiskEngine


def test_legacy_wrapper_keeps_gbpusd_distinct():
    engine = RiskEngine()
    levels = engine.calculate(
        direction="BUY",
        entry=1.27543,
        atr=0.0010,
        symbol="GBPUSD",
        timeframe="M5",
    )
    assert levels.stop_loss < levels.entry < levels.take_profit
