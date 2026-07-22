"""
Weighted confluence from technical / SMC / risk scores.
"""

from __future__ import annotations

from app.core.settings import settings


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        return {"technical": 34.0, "smc": 33.0, "risk": 33.0}
    return {k: (max(0.0, float(v)) / total) * 100.0 for k, v in weights.items()}


def calculate_confluence(
    *,
    technical_score: float,
    smc_score: float,
    risk_score: float,
    weights: dict[str, float] | None = None,
) -> float:
    resolved = _normalize_weights(weights or settings.VALIDATION_CONFLUENCE_WEIGHTS)
    total = (
        float(technical_score) * (resolved.get("technical", 0) / 100.0)
        + float(smc_score) * (resolved.get("smc", 0) / 100.0)
        + float(risk_score) * (resolved.get("risk", 0) / 100.0)
    )
    return round(max(0.0, min(100.0, total)), 2)
