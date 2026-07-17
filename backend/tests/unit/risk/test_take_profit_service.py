"""Take profit service unit tests."""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import ZoneLevel
from app.risk.take_profit_service import TakeProfitService


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="EURUSD",
        timeframe="M5",
        price=1.10000,
        atr=0.0015,
        trend="BULLISH",
        volume=100,
        avg_volume=90,
        bos_active=True,
        bos_direction="bullish",
        choch_active=False,
        choch_direction=None,
        in_premium=False,
        in_discount=True,
        equilibrium=1.09900,
        range_high=1.10500,
        range_low=1.09500,
        liquidity_targets_high=[
            ZoneLevel(price=1.10300, kind="equal_high"),
            ZoneLevel(price=1.10800, kind="previous_high"),
        ],
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_selects_nearest_liquidity_in_rr_band():
    service = TakeProfitService()
    result = service.calculate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.10000,
        stop_loss=1.09850,
        confidence=80,
    )
    # risk = 0.0015; equal_high reward 0.003 → RR=2.0 valid; previous_high farther
    assert result.at_liquidity
    assert result.take_profit == 1.10300
    assert "liquidity" in result.tp_reason.lower()


def test_rr_fallback_when_no_targets():
    service = TakeProfitService()
    result = service.calculate(
        _ctx(liquidity_targets_high=[]),
        TradeDirection.BUY,
        entry=1.10000,
        stop_loss=1.09850,
        confidence=90,
    )
    assert result.at_liquidity is False
    assert result.take_profit > 1.10000
    assert result.risk_reward >= 1.8


def test_dynamic_rr_scales_with_confidence():
    service = TakeProfitService()
    assert service.dynamic_rr(60) == 1.8
    assert service.dynamic_rr(90) == 3.0
    assert 2.0 <= service.dynamic_rr(75) <= 2.5
