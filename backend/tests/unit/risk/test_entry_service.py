"""Entry service unit tests."""

from __future__ import annotations

from app.risk.entry_service import EntryService
from app.risk.models import EntryType
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import ZoneLevel


def _ctx(**overrides) -> StructureContext:
    base = dict(
        symbol="GBPUSD",
        timeframe="M5",
        price=1.27500,
        atr=0.0012,
        trend="BULLISH",
        volume=120,
        avg_volume=100,
        bos_active=True,
        bos_direction="bullish",
        choch_active=False,
        choch_direction=None,
        in_premium=False,
        in_discount=True,
        equilibrium=1.27400,
        range_high=1.27800,
        range_low=1.27000,
        bullish_order_blocks=[
            ZoneLevel(
                price=1.27350,
                kind="order_block",
                high=1.27400,
                low=1.27300,
                direction="bullish",
            )
        ],
        atr_ok=True,
        tight_range=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_prefers_limit_at_order_block():
    service = EntryService()
    result = service.calculate(
        _ctx(),
        TradeDirection.BUY,
        stop_loss=1.27200,
    )
    assert result.entry_type == EntryType.LIMIT
    assert result.entry < 1.27500
    assert "order block" in result.entry_reason.lower()


def test_market_when_no_better_limit():
    service = EntryService()
    result = service.calculate(
        _ctx(bullish_order_blocks=[], bullish_fvgs=[], in_discount=False),
        TradeDirection.BUY,
        stop_loss=1.27200,
    )
    assert result.entry_type == EntryType.MARKET
    assert result.entry == 1.27500
