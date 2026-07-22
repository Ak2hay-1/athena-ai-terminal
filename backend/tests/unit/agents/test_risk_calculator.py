"""Unit tests for risk geometry calculator."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import numpy as np

from app.agents.risk.calculator import calculate_risk_geometry


def _candles(n: int = 60) -> list[dict]:
    rng = np.random.default_rng(3)
    start = datetime(2024, 1, 2, tzinfo=timezone.utc)
    close = 1.10 + np.cumsum(rng.normal(0, 0.0004, size=n))
    out = []
    for i in range(n):
        c = float(close[i])
        out.append(
            {
                "time": (start + timedelta(minutes=15 * i)).isoformat(),
                "open": c - 0.0001,
                "high": c + 0.0004,
                "low": c - 0.0004,
                "close": c,
                "tick_volume": 200,
            }
        )
    return out


def test_geometry_produces_sl_tp_rr_size() -> None:
    result = calculate_risk_geometry(
        symbol="EURUSD",
        timeframe="M15",
        candles=_candles(),
        technical={"trend": "Bullish", "ema_alignment": "Bullish", "score": 80},
    )
    assert result["valid"] is True
    assert result["recommended_stop_loss"] is not None
    assert result["recommended_take_profit"] is not None
    assert result["risk_reward"] > 0
    assert result["position_size"] > 0
    assert result["bias"] == "long"
    assert result["entry"] > result["recommended_stop_loss"]


def test_bearish_bias_stop_above_entry() -> None:
    result = calculate_risk_geometry(
        symbol="EURUSD",
        timeframe="H1",
        candles=_candles(),
        technical={"trend": "Bearish", "ema_alignment": "Bearish", "score": 30},
    )
    assert result["bias"] == "short"
    assert result["recommended_stop_loss"] > result["entry"]
