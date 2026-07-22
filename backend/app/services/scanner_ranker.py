"""
Deterministic scanner ranking — explainable score breakdown.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from app.schemas.scanner import ScannerScoreBreakdown


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def display_signal(raw_signal: str, confidence: int, *, strong_threshold: int = 75) -> str:
    """Map DB signal + confidence to UI signal (STRONG_* when high conviction)."""
    signal = str(raw_signal or "HOLD").upper()
    if signal == "BUY" and confidence >= strong_threshold:
        return "STRONG_BUY"
    if signal == "SELL" and confidence >= strong_threshold:
        return "STRONG_SELL"
    return signal


def session_label(now: datetime | None = None) -> str:
    """UTC session label matching frontend currentSession()."""
    hour = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).hour
    if 12 <= hour < 16:
        return "Overlap"
    if 7 <= hour < 12:
        return "London"
    if 16 <= hour < 21:
        return "New York"
    if 0 <= hour < 7:
        return "Tokyo"
    return "Sydney"


def _is_buy(signal: str) -> bool:
    return "BUY" in signal.upper()


def _is_sell(signal: str) -> bool:
    return "SELL" in signal.upper()


def _is_passive(signal: str) -> bool:
    s = signal.upper()
    return s in {"HOLD", "NEUTRAL", "NO_TRADE"}


def rank_opportunity(
    *,
    signal: str,
    confidence: int,
    trade_quality: int = 0,
    trade_probability: int = 0,
    confluence: int = 0,
    change_percent: float | None = None,
    updated_at: datetime | None = None,
    now: datetime | None = None,
    stale_threshold_minutes: int = 45,
    market_watch_change: str | None = None,
    market_watch_weight: float = 0.0,
    session: str | None = None,
) -> tuple[int, ScannerScoreBreakdown, bool, list[str]]:
    """
    Compute scanner score (0–100), breakdown, stale flag, and reason chips.

    Base: recommendation confidence
    Boosts: quality, probability, confluence, momentum alignment, freshness,
            active session, Market Watch urgency
    Penalties: HOLD/NO_TRADE, stale recommendation
    """
    now = now or datetime.now(timezone.utc)
    if updated_at is not None and updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    display = display_signal(signal, confidence)
    reasons: list[str] = []

    base = float(max(0, min(100, confidence)))
    quality = min(12.0, max(0, trade_quality) * 0.12)
    probability = min(12.0, max(0, trade_probability) * 0.12)
    conf_boost = min(10.0, max(0, confluence) * 0.10)

    momentum = 0.0
    if change_percent is not None and not _is_passive(display):
        aligned = (_is_buy(display) and change_percent > 0) or (
            _is_sell(display) and change_percent < 0
        )
        against = (_is_buy(display) and change_percent < 0) or (
            _is_sell(display) and change_percent > 0
        )
        magnitude = min(15.0, abs(change_percent) * 6.0)
        if aligned:
            momentum = magnitude
            reasons.append(f"{'+' if change_percent >= 0 else ''}{change_percent:.2f}% aligned")
        elif against:
            momentum = -min(10.0, magnitude * 0.7)

    freshness = 0.0
    stale = False
    if updated_at is not None:
        age_min = (now - updated_at).total_seconds() / 60.0
        if age_min <= 5:
            freshness = 10.0
        elif age_min <= 15:
            freshness = 7.0
        elif age_min <= stale_threshold_minutes:
            freshness = 3.0
        else:
            stale = True
            freshness = -15.0
            reasons.append("stale")
    else:
        stale = True
        freshness = -10.0

    session_name = session or session_label(now)
    session_boost = 0.0
    if session_name in {"London", "New York", "Overlap"} and not _is_passive(display):
        session_boost = 5.0 if session_name == "Overlap" else 3.0
        reasons.append(f"{session_name} session")

    mw_boost = 0.0
    if market_watch_change:
        mw_boost = min(15.0, max(0.0, market_watch_weight or 6.0))
        tag = market_watch_change.replace("_", " ")
        reasons.append(tag)

    penalties = 0.0
    sig_upper = display.upper()
    if sig_upper == "NO_TRADE":
        penalties -= 40.0
        reasons.append("no trade")
    elif sig_upper in {"HOLD", "NEUTRAL"}:
        penalties -= 25.0
        reasons.append("standby")

    if quality:
        reasons.append(f"quality {trade_quality}")
    if not reasons and not _is_passive(display):
        reasons.append(f"{display.replace('_', ' ').title()} · live")

    raw = (
        base
        + quality
        + probability
        + conf_boost
        + momentum
        + freshness
        + session_boost
        + mw_boost
        + penalties
    )
    score = int(round(_clamp(raw)))

    breakdown = ScannerScoreBreakdown(
        base=round(base, 2),
        quality=round(quality, 2),
        probability=round(probability, 2),
        confluence=round(conf_boost, 2),
        momentum_align=round(momentum, 2),
        freshness=round(freshness, 2),
        session=round(session_boost, 2),
        market_watch=round(mw_boost, 2),
        penalties=round(penalties, 2),
    )
    return score, breakdown, stale, reasons[:4]


def urgency_from_event(event: Any | None) -> tuple[str | None, float]:
    if event is None:
        return None, 0.0
    change_type = getattr(event, "change_type", None)
    weight = float(getattr(event, "weight", 0.0) or 0.0)
    if not change_type:
        return None, 0.0
    return str(change_type), weight
