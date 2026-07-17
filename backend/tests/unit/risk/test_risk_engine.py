"""Risk engine orchestrator unit tests."""

from __future__ import annotations

import pandas as pd

from app.risk.models import EntryResult
from app.risk.models import EntryType
from app.risk.models import StopLossResult
from app.risk.models import StructureContext
from app.risk.models import TakeProfitResult
from app.risk.models import ValidationFlags
from app.risk.risk_engine import RiskEngine
from app.risk.trade_validator import ValidationResult


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
        swing_lows=[162.20],
        swing_highs=[162.80],
        atr_ok=True,
        tight_range=False,
        news_high_impact=False,
    )
    base.update(overrides)
    return StructureContext(**base)


def test_sideways_returns_no_trade():
    engine = RiskEngine()
    plan = engine.build_plan(
        pd.DataFrame({"close": [1.0]}),
        symbol="EURUSD",
        timeframe="M5",
        context=_ctx(trend="SIDEWAYS"),
    )
    assert plan.signal == "NO_TRADE"


def test_buy_plan_when_services_approve(monkeypatch):
    import importlib
    from types import SimpleNamespace

    risk_mod = importlib.import_module("app.risk.risk_engine")
    engine = RiskEngine()

    monkeypatch.setattr(
        risk_mod,
        "stop_loss_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: StopLossResult(
                stop_loss=162.20,
                sl_reason="Below latest swing low with ATR buffer",
                risk_distance=0.30,
                used_structure="latest swing low",
                valid=True,
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "entry_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: EntryResult(
                entry=162.50,
                entry_type=EntryType.MARKET,
                entry_reason="Current market price",
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "take_profit_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: TakeProfitResult(
                take_profit=163.10,
                tp_reason="Previous liquidity high",
                reward_distance=0.60,
                at_liquidity=True,
                risk_reward=2.0,
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "confidence_engine",
        SimpleNamespace(score=lambda *args, **kwargs: 87),
    )
    monkeypatch.setattr(
        risk_mod,
        "trade_validator",
        SimpleNamespace(
            validate=lambda *args, **kwargs: ValidationResult(
                approved=True,
                flags=ValidationFlags(
                    trend=True,
                    bos=True,
                    choch=False,
                    volume=True,
                    atr=True,
                    liquidity=True,
                    news=True,
                    structure_sl=True,
                    risk_distance=True,
                    risk_reward=True,
                ),
                reasons=[],
            )
        ),
    )

    plan = engine.build_plan(
        pd.DataFrame({"close": [162.5]}),
        symbol="USDJPY",
        timeframe="M5",
        context=_ctx(),
    )
    assert plan.signal == "BUY"
    assert plan.entry == 162.50
    assert plan.stop_loss == 162.20
    assert plan.take_profit == 163.10
    assert plan.confidence == 87
    assert plan.sl_reason.startswith("Below")


def test_validation_failure_returns_no_trade(monkeypatch):
    import importlib
    from types import SimpleNamespace

    risk_mod = importlib.import_module("app.risk.risk_engine")
    engine = RiskEngine()

    monkeypatch.setattr(
        risk_mod,
        "stop_loss_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: StopLossResult(
                stop_loss=162.20,
                sl_reason="Below latest swing low with ATR buffer",
                risk_distance=0.30,
                used_structure="latest swing low",
                valid=True,
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "entry_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: EntryResult(
                entry=162.50,
                entry_type=EntryType.MARKET,
                entry_reason="Current market price",
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "take_profit_service",
        SimpleNamespace(
            calculate=lambda *args, **kwargs: TakeProfitResult(
                take_profit=163.10,
                tp_reason="Previous liquidity high",
                reward_distance=0.60,
                at_liquidity=True,
                risk_reward=2.0,
            )
        ),
    )
    monkeypatch.setattr(
        risk_mod,
        "confidence_engine",
        SimpleNamespace(score=lambda *args, **kwargs: 40),
    )
    monkeypatch.setattr(
        risk_mod,
        "trade_validator",
        SimpleNamespace(
            validate=lambda *args, **kwargs: ValidationResult(
                approved=False,
                flags=ValidationFlags(trend=False),
                reasons=["Trend BEARISH does not align with BUY."],
            )
        ),
    )

    plan = engine.build_plan(
        pd.DataFrame({"close": [162.5]}),
        symbol="USDJPY",
        timeframe="M5",
        context=_ctx(trend="BULLISH"),
    )
    assert plan.signal == "NO_TRADE"
    assert "Trend" in plan.reasons[0]
