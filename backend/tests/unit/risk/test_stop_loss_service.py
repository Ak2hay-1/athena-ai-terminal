"""Stop loss service unit tests."""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.stop_loss_service import StopLossService


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="USDJPY",
        timeframe="M5",
        price=162.50,
        atr=0.20,
        trend="BULLISH",
        volume=200,
        avg_volume=150,
        bos_active=True,
        bos_direction="bullish",
        choch_active=False,
        choch_direction=None,
        in_premium=False,
        in_discount=True,
        equilibrium=162.40,
        range_high=162.80,
        range_low=162.10,
        swing_highs=[162.70],
        swing_lows=[162.20],
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_buy_sl_below_swing_with_buffer():
    service = StopLossService()
    result = service.calculate(_ctx(), TradeDirection.BUY, reference_price=162.50)
    assert result.valid
    assert result.stop_loss < 162.20
    assert "swing low" in result.sl_reason.lower()
    assert result.risk_distance >= 0.15


def test_rejects_low_atr():
    service = StopLossService()
    result = service.calculate(
        _ctx(atr=0.0, atr_ok=False),
        TradeDirection.BUY,
    )
    assert result.valid is False


def test_atr_fallback_when_no_structure():
    service = StopLossService()
    result = service.calculate(
        _ctx(swing_lows=[], bullish_order_blocks=[], liquidity_sweep_lows=[]),
        TradeDirection.BUY,
        reference_price=162.50,
    )
    assert result.valid
    assert result.used_structure == "atr_fallback"
    assert result.stop_loss < 162.50
