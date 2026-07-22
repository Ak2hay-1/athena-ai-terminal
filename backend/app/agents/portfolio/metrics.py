"""
Portfolio metrics from paper position rows.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _pnl(row: dict[str, Any]) -> float:
    try:
        return float(row.get("pnl") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _rr(row: dict[str, Any]) -> float | None:
    entry = float(row.get("entry") or 0)
    sl = float(row.get("stop_loss") or 0)
    tp = float(row.get("take_profit") or 0)
    if entry <= 0 or sl <= 0 or tp <= 0:
        return None
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk <= 0:
        return None
    return reward / risk


def compute_metrics(
    positions: list[dict[str, Any]],
    *,
    account_balance: float = 10000.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=day_start.weekday())
    month_start = day_start.replace(day=1)

    open_rows = [p for p in positions if str(p.get("status") or "").upper() == "OPEN"]
    closed_rows = [
        p for p in positions if str(p.get("status") or "").upper() == "CLOSED"
    ]

    floating = sum(_pnl(p) for p in open_rows)
    closed_profit = sum(_pnl(p) for p in closed_rows)

    def _window_profit(start: datetime) -> float:
        total = 0.0
        for row in closed_rows:
            closed_at = _as_dt(row.get("closed_at"))
            if closed_at and closed_at >= start:
                total += _pnl(row)
        return round(total, 2)

    daily = _window_profit(day_start)
    weekly = _window_profit(week_start)
    monthly = _window_profit(month_start)

    wins = [r for r in closed_rows if _pnl(r) > 0]
    losses = [r for r in closed_rows if _pnl(r) < 0]
    sample = len(wins) + len(losses)
    win_rate = (len(wins) / sample * 100.0) if sample else 0.0
    loss_rate = (len(losses) / sample * 100.0) if sample else 0.0

    gross_profit = sum(_pnl(r) for r in wins)
    gross_loss = abs(sum(_pnl(r) for r in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
        float("inf") if gross_profit > 0 else 0.0
    )
    if math.isinf(profit_factor):
        profit_factor = 99.0

    rr_values = [v for v in (_rr(r) for r in closed_rows + open_rows) if v is not None]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

    exposure: dict[str, float] = defaultdict(float)
    for row in open_rows:
        symbol = str(row.get("symbol") or "?").upper()
        notional = abs(float(row.get("entry") or 0) * float(row.get("volume") or 1.0))
        exposure[symbol] += notional

    total_exposure = sum(exposure.values())
    capital_utilization = (
        (total_exposure / account_balance * 100.0) if account_balance > 0 else 0.0
    )

    equity = account_balance + closed_profit + floating
    peak = account_balance
    drawdown = 0.0
    running = account_balance
    ordered = sorted(
        closed_rows,
        key=lambda r: _as_dt(r.get("closed_at")) or now,
    )
    for row in ordered:
        running += _pnl(row)
        peak = max(peak, running)
        if peak > 0:
            dd = (peak - running) / peak * 100.0
            drawdown = max(drawdown, dd)
    if floating < 0 and equity > 0:
        drawdown = max(drawdown, abs(floating) / max(equity - floating, 1.0) * 100.0)

    # Simple Sharpe on daily closed PnL
    daily_returns: dict[str, float] = defaultdict(float)
    for row in closed_rows:
        closed_at = _as_dt(row.get("closed_at"))
        if closed_at is None:
            continue
        key = closed_at.date().isoformat()
        daily_returns[key] += _pnl(row)
    returns = list(daily_returns.values())
    sharpe = 0.0
    if len(returns) >= 2:
        mean = sum(returns) / len(returns)
        var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(var) if var > 0 else 0.0
        if std > 0:
            sharpe = (mean / std) * math.sqrt(252)

    return {
        "open_trades": len(open_rows),
        "closed_trades": len(closed_rows),
        "daily_profit": daily,
        "weekly_profit": weekly,
        "monthly_profit": monthly,
        "floating_profit": round(floating, 2),
        "closed_profit": round(closed_profit, 2),
        "risk_exposure": {k: round(v, 2) for k, v in exposure.items()},
        "total_exposure": round(total_exposure, 2),
        "capital_utilization": round(capital_utilization, 2),
        "drawdown": round(drawdown, 2),
        "average_rr": round(avg_rr, 2),
        "win_rate": round(win_rate, 2),
        "loss_rate": round(loss_rate, 2),
        "sharpe_ratio": round(sharpe, 2),
        "profit_factor": round(profit_factor, 2),
        "equity": round(equity, 2),
        "account_balance": account_balance,
        "sample_size": sample,
    }
