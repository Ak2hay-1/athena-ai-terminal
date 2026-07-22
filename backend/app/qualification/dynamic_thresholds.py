"""Session / regime / volatility adaptive thresholds."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from app.core.settings import settings
from app.qualification.models import MarketRegime


def trading_session(now: datetime | None = None) -> str:
    """UTC session label for threshold adaptation."""
    hour = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).hour
    if 12 <= hour < 16:
        return "Overlap"
    if 7 <= hour < 12:
        return "London"
    if 16 <= hour < 21:
        return "New York"
    if 0 <= hour < 7:
        return "Asian"
    return "Sydney"


def resolve_thresholds(
    *,
    regime: str,
    session: str | None = None,
    historical_win_rate: float | None = None,
) -> dict[str, float]:
    """
    Adaptive minimums for qualification and ranking.

    Returns keys: min_quality, min_confidence, min_adx, min_atr_fraction,
    min_volume_ratio, min_rr, min_structure_score.
    """
    session_name = session or trading_session()
    session_cfg = dict(settings.QUAL_SESSION_THRESHOLDS.get(session_name) or {})
    regime_cfg = dict(settings.QUAL_REGIME_THRESHOLDS.get(regime) or {})

    base = {
        "min_quality": float(settings.MIN_SETUP_QUALITY),
        "min_confidence": float(settings.MIN_CONFIDENCE),
        "min_adx": float(settings.QUAL_MIN_ADX),
        "min_atr_fraction": float(settings.ATR_MIN_FRACTION_OF_PRICE),
        "min_volume_ratio": float(settings.VOLUME_MIN_RATIO),
        "min_rr": float(settings.MIN_RR),
        "min_structure_score": float(settings.QUAL_MIN_STRUCTURE_SCORE),
    }

    # Session overrides (e.g. Asian requires higher quality)
    for key, value in session_cfg.items():
        if key in base and value is not None:
            base[key] = float(value)

    # Regime overlays — low vol / ranging are stricter; expansion/breakout looser on ADX
    for key, value in regime_cfg.items():
        if key in base and value is not None:
            base[key] = float(value)

    regime_u = (regime or "").upper()
    if regime_u == MarketRegime.LOW_VOLATILITY.value:
        base["min_quality"] = max(base["min_quality"], float(settings.QUAL_LOW_VOL_MIN_QUALITY))
    if regime_u == MarketRegime.HIGH_VOLATILITY.value:
        base["min_quality"] = min(base["min_quality"], float(settings.QUAL_HIGH_VOL_MIN_QUALITY))
    if regime_u == MarketRegime.RANGING.value:
        base["min_adx"] = max(base["min_adx"], float(settings.QUAL_RANGING_MIN_ADX))

    if historical_win_rate is not None and historical_win_rate > 0:
        # Strong historical edge slightly relaxes quality floor (capped)
        if historical_win_rate >= 65:
            base["min_quality"] = max(
                float(settings.QUAL_FLOOR_MIN_QUALITY),
                base["min_quality"] - 5,
            )
        elif historical_win_rate < 40:
            base["min_quality"] = min(95.0, base["min_quality"] + 5)

    return base
