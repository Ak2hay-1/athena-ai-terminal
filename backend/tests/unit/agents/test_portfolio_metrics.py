"""Unit tests for portfolio metrics and health score."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.agents.portfolio.health import portfolio_health_score
from app.agents.portfolio.metrics import compute_metrics
from app.agents.portfolio.recommendations import build_recommendations


def _closed(pnl: float, days_ago: int = 0, symbol: str = "EURUSD") -> dict:
    now = datetime.now(timezone.utc)
    return {
        "status": "CLOSED",
        "symbol": symbol,
        "signal": "BUY",
        "entry": 1.1,
        "stop_loss": 1.09,
        "take_profit": 1.12,
        "volume": 1.0,
        "pnl": pnl,
        "closed_at": (now - timedelta(days=days_ago)).isoformat(),
        "opened_at": (now - timedelta(days=days_ago, hours=1)).isoformat(),
    }


def test_metrics_win_rate_and_profit_factor() -> None:
    positions = [
        _closed(100, 0),
        _closed(50, 0),
        _closed(-40, 1),
        {
            "status": "OPEN",
            "symbol": "EURUSD",
            "signal": "BUY",
            "entry": 1.1,
            "stop_loss": 1.09,
            "take_profit": 1.12,
            "volume": 1.0,
            "pnl": 10,
        },
    ]
    metrics = compute_metrics(positions, account_balance=10000)
    assert metrics["closed_trades"] == 3
    assert metrics["open_trades"] == 1
    assert metrics["win_rate"] == round(2 / 3 * 100, 2)
    assert metrics["profit_factor"] > 1
    assert metrics["daily_profit"] == 150.0
    assert 0 <= metrics["drawdown"] <= 100


def test_health_score_bounds_and_recommendations() -> None:
    metrics = compute_metrics(
        [_closed(-200, 0), _closed(-150, 0), _closed(-100, 1)],
        account_balance=10000,
    )
    health = portfolio_health_score(metrics)
    assert 0 <= health <= 100
    tips = build_recommendations(metrics, health)
    codes = {t["code"] for t in tips}
    assert "reduce_risk" in codes or "recover_after_losses" in codes or "avoid_trading_today" in codes
