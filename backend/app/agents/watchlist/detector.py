"""
Watchlist opportunity detection.
"""

from __future__ import annotations

from typing import Any

from app.core.settings import settings


def is_opportunity(payload: dict[str, Any], *, event_type: str) -> bool:
    min_conf = float(settings.WATCHLIST_MIN_CONFLUENCE)
    status = str(payload.get("status") or "").upper()
    confluence = float(
        payload.get("confluence")
        or payload.get("score")
        or payload.get("confidence")
        or 0.0
    )

    if event_type.endswith("TradeValidationCompleted") or event_type == "TradeValidationCompleted":
        if status not in {"APPROVED", "WAIT"}:
            return False
        return confluence >= min_conf

    if event_type.endswith("TechnicalAnalysisCompleted") or event_type == "TechnicalAnalysisCompleted":
        return confluence >= min_conf

    return False


def opportunity_payload(
    base: dict[str, Any],
    *,
    user_id: int,
    event_type: str,
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "symbol": str(base.get("symbol") or "").upper(),
        "timeframe": str(base.get("timeframe") or "").upper(),
        "status": base.get("status"),
        "confluence": float(
            base.get("confluence") or base.get("score") or base.get("confidence") or 0.0
        ),
        "scores": base.get("scores") or {},
        "bias": base.get("bias") or base.get("signal"),
        "source_event": event_type,
        "evidence": base.get("evidence") or base.get("reasons") or [],
    }
