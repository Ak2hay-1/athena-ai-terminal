"""Risk trade validator unit tests."""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.trade_validator import TradeValidator


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
        equilibrium=162.4,
        range_high=162.9,
        range_low=162.0,
        atr_ok=True,
        tight_range=False,
        news_high_impact=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_approves_aligned_setup():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=162.50,
        stop_loss=162.20,
        take_profit=163.10,
        risk_reward=2.0,
        used_structure="latest swing low",
        at_liquidity_tp=True,
    )
    assert result.approved is True


def test_rejects_trend_misalignment():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(trend="BEARISH"),
        TradeDirection.BUY,
        entry=162.50,
        stop_loss=162.20,
        take_profit=163.10,
        risk_reward=2.0,
        used_structure="latest swing low",
        at_liquidity_tp=True,
    )
    assert result.approved is False
    assert result.flags.trend is False


def test_rejects_high_impact_news():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(news_high_impact=True),
        TradeDirection.BUY,
        entry=162.50,
        stop_loss=162.20,
        take_profit=163.10,
        risk_reward=2.0,
        used_structure="latest swing low",
        at_liquidity_tp=True,
    )
    assert result.approved is False
    assert result.flags.news is False


def test_rejects_poor_rr():
    validator = TradeValidator()
    result = validator.validate(
        _ctx(),
        TradeDirection.BUY,
        entry=162.50,
        stop_loss=162.20,
        take_profit=162.55,
        risk_reward=0.16,
        used_structure="latest swing low",
        at_liquidity_tp=False,
    )
    assert result.approved is False
    assert result.flags.risk_reward is False
