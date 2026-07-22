"""
Deterministic portfolio recommendations.
"""

from __future__ import annotations

from typing import Any


def build_recommendations(metrics: dict[str, Any], health: float) -> list[dict[str, str]]:
    tips: list[dict[str, str]] = []
    drawdown = float(metrics.get("drawdown") or 0.0)
    util = float(metrics.get("capital_utilization") or 0.0)
    win_rate = float(metrics.get("win_rate") or 0.0)
    sample = int(metrics.get("sample_size") or 0)
    daily = float(metrics.get("daily_profit") or 0.0)
    exposure = metrics.get("risk_exposure") or {}
    open_trades = int(metrics.get("open_trades") or 0)

    if drawdown >= 12 or util > 65 or health < 45:
        tips.append(
            {
                "code": "reduce_risk",
                "title": "Reduce risk",
                "detail": "Drawdown or capital utilization is elevated; cut size and open risk.",
            }
        )

    if (
        health >= 75
        and util < 35
        and open_trades <= 2
        and (sample < 5 or win_rate >= 55)
    ):
        tips.append(
            {
                "code": "increase_position_size",
                "title": "Increase position size",
                "detail": "Health is strong and utilization is low; modest size increase is reasonable.",
            }
        )

    if daily < 0 and (sample >= 3 and win_rate < 40):
        tips.append(
            {
                "code": "avoid_trading_today",
                "title": "Avoid trading today",
                "detail": "Recent results are weak; pause discretionary entries for the session.",
            }
        )

    if daily < 0 or drawdown >= 8:
        tips.append(
            {
                "code": "recover_after_losses",
                "title": "Recover after losses",
                "detail": "Trade smaller, wait for A+ confluence, and avoid revenge sizing.",
            }
        )

    if isinstance(exposure, dict) and len(exposure) == 1 and open_trades >= 2:
        tips.append(
            {
                "code": "diversify",
                "title": "Diversification suggestions",
                "detail": "Exposure is concentrated in one symbol; spread risk across uncorrelated pairs.",
            }
        )
    elif isinstance(exposure, dict) and exposure:
        total = sum(float(v) for v in exposure.values()) or 1.0
        top = max(exposure.items(), key=lambda kv: float(kv[1]))
        if float(top[1]) / total > 0.6:
            tips.append(
                {
                    "code": "diversify",
                    "title": "Diversification suggestions",
                    "detail": f"{top[0]} dominates exposure; consider reducing concentration.",
                }
            )

    if not tips:
        tips.append(
            {
                "code": "maintain",
                "title": "Maintain discipline",
                "detail": "Portfolio metrics are balanced; keep current risk rules.",
            }
        )
    return tips
