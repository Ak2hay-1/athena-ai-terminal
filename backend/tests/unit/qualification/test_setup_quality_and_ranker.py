"""Setup quality, ranking, correlation, lifecycle tests."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.qualification.correlation_filter import filter_correlated
from app.qualification.correlation_filter import is_correlated
from app.qualification.portfolio_awareness import evaluate_portfolio_fit
from app.qualification.recommendation_ranker import rank_opportunities
from app.qualification.rejection_reasons import build_rejection_checklist
from app.qualification.rejection_reasons import format_rejection_summary
from app.qualification.setup_lifecycle import should_create_new
from app.qualification.setup_quality import SetupQualityService
from app.qualification.setup_quality import grade_for_score
from app.qualification.models import GateCheck
from app.qualification.models import SetupQualityGrade


def test_setup_quality_grades():
    assert grade_for_score(95) == SetupQualityGrade.ELITE
    assert grade_for_score(82) == SetupQualityGrade.EXCELLENT
    assert grade_for_score(72) == SetupQualityGrade.GOOD
    assert grade_for_score(65) == SetupQualityGrade.WATCHLIST
    assert grade_for_score(40) == SetupQualityGrade.NO_TRADE


def test_setup_quality_scoring_components():
    result = SetupQualityService().score(
        trend_strength=35,
        structure_score=80,
        volume_ratio=1.2,
        risk_reward=2.5,
        atr_ok=True,
        session="London",
        bos_active=True,
        confluence=70,
    )
    assert 0 <= result.score <= 100
    assert "trend_strength" in result.components
    assert sum(result.components.values()) == result.score or abs(
        sum(result.components.values()) - result.score
    ) <= 1


def test_ranker_limits_actionable():
    items = [
        {
            "symbol": f"SYM{i}",
            "timeframe": "M15",
            "signal": "BUY",
            "setup_quality": 90 - i,
            "confidence": 80,
            "risk_reward": 2.5,
            "trend_strength": 30,
            "historical_win_rate": 55,
        }
        for i in range(8)
    ]
    ranked = rank_opportunities(items, max_actionable=3, max_watchlist=8, min_setup_quality=70)
    actionable = [r for r in ranked if r.signal in {"BUY", "SELL"}]
    assert len(actionable) <= 3


def test_correlation_usd_majors():
    assert is_correlated("EURUSD", "BUY", "GBPUSD", "BUY") is True
    assert is_correlated("EURUSD", "BUY", "USDJPY", "BUY") is False

    rows = filter_correlated(
        [
            {"symbol": "EURUSD", "signal": "BUY", "setup_quality": 90, "confidence": 80},
            {"symbol": "GBPUSD", "signal": "BUY", "setup_quality": 80, "confidence": 75},
            {"symbol": "AUDUSD", "signal": "BUY", "setup_quality": 70, "confidence": 70},
        ]
    )
    buys = [r for r in rows if r["signal"] == "BUY"]
    correlated = [r for r in rows if r.get("correlated")]
    assert len(buys) == 1
    assert len(correlated) == 2


def test_lifecycle_update_when_levels_similar():
    existing = {
        "signal": "BUY",
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "lifecycle_state": "ACTIVE",
        "created_at": datetime.now(timezone.utc),
    }
    create, action = should_create_new(
        existing=existing,
        new_signal="BUY",
        new_entry=1.1001,
        new_sl=1.0951,
        new_tp=1.1101,
        atr=0.0010,
    )
    assert create is False
    assert action == "update"


def test_lifecycle_expire():
    existing = {
        "signal": "BUY",
        "entry_price": 1.1000,
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "lifecycle_state": "ACTIVE",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=10),
    }
    create, action = should_create_new(
        existing=existing,
        new_signal="BUY",
        new_entry=1.1000,
        new_sl=1.0950,
        new_tp=1.1100,
        atr=0.0010,
    )
    assert create is True
    assert action == "expire"


def test_rejection_checklist_format():
    gates = [
        GateCheck(name="Trend Strength", passed=True, detail="ADX=32"),
        GateCheck(name="Liquidity", passed=False, detail="ratio=0.4"),
    ]
    checklist = build_rejection_checklist(gates)
    lines = format_rejection_summary(checklist)
    assert lines[0].startswith("✓")
    assert lines[1].startswith("✗")


def test_portfolio_max_buys():
    open_trades = [
        {"symbol": "EURUSD", "signal": "BUY"},
        {"symbol": "GBPUSD", "signal": "BUY"},
        {"symbol": "AUDUSD", "signal": "BUY"},
    ]
    allowed, reasons = evaluate_portfolio_fit(
        symbol="NZDUSD",
        signal="BUY",
        open_trades=open_trades,
    )
    # Either max buys or correlation should reject
    assert allowed is False
    assert reasons
