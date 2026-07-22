"""Unit tests for institutional recommendation enrichment services."""

from __future__ import annotations

from app.risk.confidence_engine import ConfidenceEngine
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.risk.models import ValidationFlags
from app.risk.models import ZoneLevel
from app.services.confidence_breakdown_service import ConfidenceBreakdownService
from app.services.entry_zone_service import EntryZoneService
from app.services.institutional_checklist_service import InstitutionalChecklistService
from app.services.market_heatmap_service import MarketHeatmapService


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
        bullish_order_blocks=[
            ZoneLevel(price=1.095, kind="order_block", high=1.096, low=1.094),
        ],
        bullish_fvgs=[
            ZoneLevel(price=1.0945, kind="fvg", high=1.0955, low=1.0935),
        ],
        liquidity_targets_high=[ZoneLevel(price=1.11, kind="equal_high")],
        liquidity_sweep_lows=[1.085],
        multi_tf_trend="BULLISH",
        news_high_impact=False,
        news_sentiment=0.4,
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_score_components_sum_matches_score():
    engine = ConfidenceEngine()
    ctx = _ctx()
    components = engine.score_components(
        ctx,
        TradeDirection.BUY,
        at_liquidity_tp=True,
        structure_sl=True,
        risk_reward=2.5,
    )
    score = engine.score(
        ctx,
        TradeDirection.BUY,
        at_liquidity_tp=True,
        structure_sl=True,
        risk_reward=2.5,
    )
    assert abs(sum(components.values()) - score) < 0.51
    assert sum(engine.WEIGHTS.values()) == 100


def test_confidence_breakdown_sums_to_confidence():
    service = ConfidenceBreakdownService()
    ctx = _ctx()
    plan = TradePlan(
        signal="BUY",
        confidence=86,
        trend="BULLISH",
        risk_reward=2.0,
        tp_reason="Previous liquidity high",
        validation=ValidationFlags(
            structure_sl=True,
            liquidity=True,
            risk_reward=True,
        ),
    )
    # Force target via plan.confidence after computing real components.
    engine = ConfidenceEngine()
    real = engine.score(
        ctx,
        TradeDirection.BUY,
        at_liquidity_tp=True,
        structure_sl=True,
        risk_reward=2.0,
    )
    plan.confidence = real
    breakdown = service.build(ctx, plan)
    total = (
        breakdown.trend
        + breakdown.momentum
        + breakdown.structure
        + breakdown.liquidity
        + breakdown.news
        + breakdown.risk
    )
    assert total == real
    assert breakdown.trend_max == 35
    assert breakdown.structure_max == 20


def test_checklist_from_flags_and_structure():
    service = InstitutionalChecklistService()
    ctx = _ctx()
    plan = TradePlan(
        signal="BUY",
        trend="BULLISH",
        validation=ValidationFlags(
            trend=True,
            bos=True,
            choch=True,
            atr=True,
            risk_reward=True,
            news=True,
        ),
    )
    items = service.build(ctx, plan)
    assert len(items) == 9
    by_name = {i.name: i.passed for i in items}
    assert by_name["BOS Confirmed"] is True
    assert by_name["CHOCH Confirmed"] is True
    assert by_name["Order Block"] is True
    assert by_name["Fair Value Gap"] is True
    assert by_name["Liquidity Sweep"] is True
    assert by_name["ATR Validation"] is True
    assert by_name["News Filter"] is True


def test_checklist_fails_missing_sweep():
    service = InstitutionalChecklistService()
    ctx = _ctx(liquidity_sweep_lows=[])
    plan = TradePlan(
        signal="BUY",
        trend="BULLISH",
        validation=ValidationFlags(bos=True, atr=True, news=True, risk_reward=True),
    )
    items = service.build(ctx, plan)
    sweep = next(i for i in items if i.name == "Liquidity Sweep")
    assert sweep.passed is False


def test_heatmap_bounds():
    service = MarketHeatmapService()
    ctx = _ctx()
    plan = TradePlan(
        signal="BUY",
        trend="BULLISH",
        risk_reward=2.0,
        validation=ValidationFlags(
            structure_sl=True,
            risk_reward=True,
            atr=True,
            risk_distance=True,
        ),
    )
    heatmap = service.build(
        ctx,
        plan,
        analysis={
            "indicators": {
                "rsi": 62,
                "macd": {"value": 0.1, "signal": 0.05, "bullish": True},
            },
        },
    )
    for value in (
        heatmap.trend,
        heatmap.momentum,
        heatmap.structure,
        heatmap.liquidity,
        heatmap.volatility,
        heatmap.news,
        heatmap.risk,
    ):
        assert 0 <= value <= 100


def test_entry_zone_buy_uses_order_block():
    service = EntryZoneService()
    ctx = _ctx()
    plan = TradePlan(
        signal="BUY",
        entry=1.095,
        trend="BULLISH",
    )
    zone = service.build(ctx, plan)
    assert zone.aggressive > 0
    assert zone.optimal_low > 0
    assert zone.optimal_high >= zone.optimal_low
    assert zone.conservative > 0
    # Conservative should be at/ below aggressive for buys after ordering.
    assert zone.conservative <= zone.aggressive


def test_entry_zone_sell_ordering():
    service = EntryZoneService()
    ctx = _ctx(
        trend="BEARISH",
        in_premium=True,
        in_discount=False,
        bullish_order_blocks=[],
        bullish_fvgs=[],
        bearish_order_blocks=[
            ZoneLevel(price=1.105, kind="order_block", high=1.106, low=1.104),
        ],
        bos_direction="bearish",
        choch_direction="bearish",
        multi_tf_trend="BEARISH",
    )
    plan = TradePlan(signal="SELL", entry=1.105, trend="BEARISH")
    zone = service.build(ctx, plan)
    assert zone.aggressive > 0
    assert zone.optimal_high >= zone.optimal_low
