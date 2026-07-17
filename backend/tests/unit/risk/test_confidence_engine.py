"""Confidence engine unit tests."""

from __future__ import annotations

from app.risk.confidence_engine import ConfidenceEngine
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import ZoneLevel


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="EURUSD",
        timeframe="M15",
        price=1.10,
        atr=0.002,
        trend="BULLISH",
        volume=200,
        avg_volume=100,
        bos_active=True,
        bos_direction="bullish",
        choch_active=True,
        choch_direction="bullish",
        in_premium=False,
        in_discount=True,
        equilibrium=1.09,
        range_high=1.12,
        range_low=1.08,
        bullish_order_blocks=[ZoneLevel(price=1.095, kind="order_block")],
        liquidity_targets_high=[ZoneLevel(price=1.11, kind="equal_high")],
        multi_tf_trend="BULLISH",
        news_high_impact=False,
        news_sentiment=0.4,
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_high_quality_setup_scores_high():
    engine = ConfidenceEngine()
    score = engine.score(
        _ctx(),
        TradeDirection.BUY,
        at_liquidity_tp=True,
        structure_sl=True,
        risk_reward=2.5,
    )
    assert score >= 70
    assert score <= 100


def test_counter_trend_and_news_block_reduce_score():
    engine = ConfidenceEngine()
    score = engine.score(
        _ctx(trend="BEARISH", news_high_impact=True, multi_tf_trend="BEARISH"),
        TradeDirection.BUY,
        structure_sl=False,
        risk_reward=1.0,
    )
    assert score < 50


def test_weights_sum_to_100():
    engine = ConfidenceEngine()
    assert sum(engine.WEIGHTS.values()) == 100
