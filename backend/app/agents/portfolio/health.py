"""
Portfolio health score 0–100.
"""

from __future__ import annotations

from typing import Any


def portfolio_health_score(metrics: dict[str, Any]) -> float:
    score = 70.0

    drawdown = float(metrics.get("drawdown") or 0.0)
    if drawdown >= 25:
        score -= 30
    elif drawdown >= 15:
        score -= 20
    elif drawdown >= 8:
        score -= 10
    else:
        score += 5

    win_rate = float(metrics.get("win_rate") or 0.0)
    sample = int(metrics.get("sample_size") or 0)
    if sample >= 5:
        if win_rate >= 60:
            score += 10
        elif win_rate >= 50:
            score += 5
        elif win_rate < 40:
            score -= 15
        elif win_rate < 45:
            score -= 8

    util = float(metrics.get("capital_utilization") or 0.0)
    if util > 80:
        score -= 20
    elif util > 60:
        score -= 10
    elif 20 <= util <= 50:
        score += 5

    exposure = metrics.get("risk_exposure") or {}
    if isinstance(exposure, dict) and exposure:
        total = sum(float(v) for v in exposure.values()) or 1.0
        max_share = max(float(v) for v in exposure.values()) / total * 100.0
        if max_share > 70:
            score -= 15
        elif max_share > 50:
            score -= 8

    pf = float(metrics.get("profit_factor") or 0.0)
    if pf >= 1.5:
        score += 8
    elif pf > 0 and pf < 1.0:
        score -= 10

    daily = float(metrics.get("daily_profit") or 0.0)
    if daily < 0 and abs(daily) > float(metrics.get("account_balance") or 10000) * 0.02:
        score -= 10

    return round(max(0.0, min(100.0, score)), 1)
