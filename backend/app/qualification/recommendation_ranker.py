"""
Opportunity ranking — quality over quantity.

After symbols are analyzed, keep only the best actionable setups.
"""

from __future__ import annotations

from typing import Any
from typing import Iterable

from app.core.settings import settings
from app.qualification.models import RankedOpportunity
from app.qualification.models import ScannerQualityGroup
from app.qualification.setup_quality import scanner_group_for_score


def _rank_score(
    *,
    setup_quality: int,
    confidence: int,
    risk_reward: float,
    trend_strength: float,
    historical_win_rate: int,
) -> float:
    rr = max(0.0, float(risk_reward))
    rr_norm = min(100.0, (rr / max(float(settings.PREFERRED_RR), 0.01)) * 100.0)
    adx_norm = min(100.0, float(trend_strength))
    return (
        setup_quality * 0.40
        + confidence * 0.25
        + rr_norm * 0.15
        + adx_norm * 0.10
        + float(historical_win_rate) * 0.10
    )


def rank_opportunities(
    items: Iterable[dict[str, Any]],
    *,
    max_actionable: int | None = None,
    max_watchlist: int | None = None,
    min_setup_quality: int | None = None,
    min_confidence: int | None = None,
) -> list[RankedOpportunity]:
    """
    Rank analyzed setups and classify into elite / high_quality / watchlist / no_trade.

    Input dict keys (flexible):
      symbol, timeframe, signal, setup_quality, confidence, risk_reward,
      trend_strength, historical_win_rate
    """
    max_act = (
        int(settings.MAX_ACTIONABLE_TRADES)
        if max_actionable is None
        else int(max_actionable)
    )
    max_watch = (
        int(settings.MAX_WATCHLIST) if max_watchlist is None else int(max_watchlist)
    )
    min_q = (
        int(settings.MIN_SETUP_QUALITY)
        if min_setup_quality is None
        else int(min_setup_quality)
    )
    min_c = (
        int(settings.MIN_CONFIDENCE) if min_confidence is None else int(min_confidence)
    )

    ranked: list[RankedOpportunity] = []
    for raw in items:
        signal = str(raw.get("signal") or "NO_TRADE").upper()
        quality = int(raw.get("setup_quality") or raw.get("trade_quality") or 0)
        confidence = int(raw.get("confidence") or 0)
        rr = float(raw.get("risk_reward") or 0.0)
        trend_strength = float(raw.get("trend_strength") or 0.0)
        hist = int(raw.get("historical_win_rate") or 0)
        score = _rank_score(
            setup_quality=quality,
            confidence=confidence,
            risk_reward=rr,
            trend_strength=trend_strength,
            historical_win_rate=hist,
        )
        group = scanner_group_for_score(quality, signal)

        actionable = signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}
        if actionable and (quality < min_q or confidence < min_c):
            if quality >= 60:
                signal = "HOLD"
                group = ScannerQualityGroup.WATCHLIST.value
            else:
                signal = "NO_TRADE"
                group = ScannerQualityGroup.NO_TRADE.value

        ranked.append(
            RankedOpportunity(
                symbol=str(raw.get("symbol") or ""),
                timeframe=str(raw.get("timeframe") or ""),
                signal=signal,
                setup_quality=quality,
                confidence=confidence,
                risk_reward=rr,
                trend_strength=trend_strength,
                historical_win_rate=hist,
                rank_score=score,
                group=group,
            )
        )

    ranked.sort(key=lambda r: (r.rank_score, r.setup_quality, r.confidence), reverse=True)

    actionable_count = 0
    watchlist_count = 0
    result: list[RankedOpportunity] = []

    for item in ranked:
        if item.signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
            if actionable_count >= max_act:
                # Demote excess to watchlist / no_trade
                if watchlist_count < max_watch and item.setup_quality >= 60:
                    item.signal = "HOLD"
                    item.group = ScannerQualityGroup.WATCHLIST.value
                    watchlist_count += 1
                else:
                    item.signal = "NO_TRADE"
                    item.group = ScannerQualityGroup.NO_TRADE.value
            else:
                actionable_count += 1
                if item.setup_quality >= 90:
                    item.group = ScannerQualityGroup.ELITE.value
                else:
                    item.group = ScannerQualityGroup.HIGH_QUALITY.value
        elif item.group == ScannerQualityGroup.WATCHLIST.value:
            if watchlist_count >= max_watch:
                item.signal = "NO_TRADE"
                item.group = ScannerQualityGroup.NO_TRADE.value
            else:
                watchlist_count += 1
        result.append(item)

    return result


def apply_global_limits_to_recommendation(
    *,
    signal: str,
    setup_quality: int,
    confidence: int,
    peer_actionable_count: int,
) -> tuple[str, str]:
    """
    Single-symbol post-check against global actionable cap using peer count.

    Returns (signal, scanner_group).
    """
    max_act = int(settings.MAX_ACTIONABLE_TRADES)
    min_q = int(settings.MIN_SETUP_QUALITY)
    min_c = int(settings.MIN_CONFIDENCE)
    sig = signal.upper()

    if sig not in {"BUY", "SELL"}:
        return sig, scanner_group_for_score(setup_quality, sig)

    if setup_quality < 60:
        return "NO_TRADE", ScannerQualityGroup.NO_TRADE.value
    if setup_quality < min_q or confidence < min_c:
        return "HOLD", ScannerQualityGroup.WATCHLIST.value
    if peer_actionable_count >= max_act:
        return "HOLD", ScannerQualityGroup.WATCHLIST.value

    group = (
        ScannerQualityGroup.ELITE.value
        if setup_quality >= 90
        else ScannerQualityGroup.HIGH_QUALITY.value
    )
    return sig, group
