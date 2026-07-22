"""TradeValidator hard-gate regressions for institutional desk."""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.trade_validator import TradeValidator


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="EURUSD",
        timeframe="M15",
        price=1.1000,
        atr=0.0010,
        trend="BULLISH",
        volume=200,
        avg_volume=150,
        bos_active=True,
        bos_direction="bullish",
        choch_active=False,
        choch_direction=None,
        in_premium=False,
        in_discount=True,
        equilibrium=1.0990,
        range_high=1.1050,
        range_low=1.0950,
        atr_ok=True,
        tight_range=False,
        news_high_impact=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_rejects_weak_trend_strength():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        risk_reward=2.0,
        used_structure="swing low",
        at_liquidity_tp=True,
        trend_strength=10.0,
    )
    assert result.approved is False
    assert result.flags.trend is False


def test_rejects_incompatible_regime():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        risk_reward=2.0,
        used_structure="swing low",
        at_liquidity_tp=True,
        market_regime="RANGING",
        trend_strength=30.0,
    )
    assert result.approved is False
    assert result.flags.regime is False


def test_rejects_high_spread():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        risk_reward=2.0,
        used_structure="swing low",
        at_liquidity_tp=True,
        spread=0.0020,
        trend_strength=30.0,
        market_regime="TRENDING",
    )
    assert result.approved is False
    assert result.flags.spread is False


def test_rejects_mtf_disagreement():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        risk_reward=2.0,
        used_structure="swing low",
        at_liquidity_tp=True,
        mtf_aligned=False,
        trend_strength=30.0,
        market_regime="TRENDING",
    )
    assert result.approved is False
    assert result.flags.mtf is False


def test_rejects_rr_below_minimum():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=1.1000,
        stop_loss=1.0970,
        take_profit=1.1010,
        risk_reward=0.8,
        used_structure="swing low",
        at_liquidity_tp=False,
        trend_strength=30.0,
        market_regime="TRENDING",
    )
    assert result.approved is False
    assert result.flags.risk_reward is False
