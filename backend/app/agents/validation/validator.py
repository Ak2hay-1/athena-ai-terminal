"""
Trade validation evidence — APPROVED / REJECTED / WAIT (not execution).
"""

from __future__ import annotations

from typing import Any

from app.agents.validation.confluence import calculate_confluence
from app.core.settings import settings

_BLOCKING_WARNINGS = frozenset({"news_risk", "weekend", "holiday"})


def validate_trade_evidence(
    *,
    technical_score: float,
    smc_score: float,
    risk_score: float,
    risk_reward: float,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """
    Apply configurable thresholds and return status + reasons.
    """
    warnings = list(warnings or [])
    reasons: list[str] = []
    min_tech = float(settings.VALIDATION_MIN_TECHNICAL_SCORE)
    min_smc = float(settings.VALIDATION_MIN_SMC_SCORE)
    min_risk = float(settings.VALIDATION_MIN_RISK_SCORE)
    min_rr = float(settings.VALIDATION_MIN_RR)
    min_conf = float(settings.VALIDATION_MIN_CONFLUENCE)

    hard_fail = False

    if technical_score < min_tech:
        hard_fail = True
        reasons.append("Trend weak" if technical_score < min_tech - 10 else "Technical score below minimum")
    if smc_score < min_smc:
        hard_fail = True
        reasons.append("Liquidity not swept" if smc_score < min_smc else "SMC score below minimum")
    if risk_score < min_risk:
        hard_fail = True
        if "extreme_atr" in warnings:
            reasons.append("ATR too high")
        else:
            reasons.append("Risk score below minimum")
    if risk_reward < min_rr:
        hard_fail = True
        reasons.append("Poor RR")

    for warning in warnings:
        if warning in _BLOCKING_WARNINGS:
            hard_fail = True
            if warning == "news_risk":
                reasons.append("News risk")
            elif warning == "weekend":
                reasons.append("Weekend")
            elif warning == "holiday":
                reasons.append("Holiday")

    confluence = calculate_confluence(
        technical_score=technical_score,
        smc_score=smc_score,
        risk_score=risk_score,
    )

    borderline = (
        (min_tech <= technical_score < min_tech + 5)
        or (min_smc <= smc_score < min_smc + 5)
        or (min_risk <= risk_score < min_risk + 5)
        or (min_conf <= confluence < min_conf + 5)
    )

    if hard_fail:
        status = "REJECTED"
        approval = False
    elif confluence < min_conf or borderline:
        status = "WAIT"
        approval = False
        if confluence < min_conf:
            reasons.append("Confluence below minimum")
        elif borderline:
            reasons.append("Scores near threshold — wait for confirmation")
    else:
        status = "APPROVED"
        approval = True
        if not reasons:
            reasons.append("All validation thresholds met")

    # Deduplicate reasons preserving order
    seen: set[str] = set()
    unique_reasons: list[str] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            unique_reasons.append(reason)

    return {
        "status": status,
        "approval": approval,
        "confluence": confluence,
        "validation_score": confluence,
        "reasons": unique_reasons,
        "scores": {
            "technical": technical_score,
            "smc": smc_score,
            "risk": risk_score,
            "risk_reward": risk_reward,
        },
    }
