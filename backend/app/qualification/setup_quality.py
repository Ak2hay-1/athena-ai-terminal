"""
Setup Quality Score — separate from confidence.

Confidence = certainty of analysis.
Setup Quality = quality of the opportunity.
"""

from __future__ import annotations

from typing import Any

from app.core.settings import settings
from app.qualification.dynamic_thresholds import trading_session
from app.qualification.models import GateCheck
from app.qualification.models import ScannerQualityGroup
from app.qualification.models import SetupQualityGrade
from app.qualification.models import SetupQualityResult


# Component max weights (sum = 100)
WEIGHTS = {
    "trend_strength": 20,
    "structure": 20,
    "liquidity": 15,
    "momentum": 15,
    "risk_reward": 15,
    "volatility": 10,
    "session": 5,
}


def grade_for_score(score: int) -> SetupQualityGrade:
    if score >= 90:
        return SetupQualityGrade.ELITE
    if score >= 80:
        return SetupQualityGrade.EXCELLENT
    if score >= 70:
        return SetupQualityGrade.GOOD
    if score >= 60:
        return SetupQualityGrade.WATCHLIST
    return SetupQualityGrade.NO_TRADE


def scanner_group_for_score(score: int, signal: str | None = None) -> str:
    sig = (signal or "").upper()
    if sig in {"NO_TRADE", "HOLD"} and score < 60:
        return ScannerQualityGroup.NO_TRADE.value
    if score >= 90:
        return ScannerQualityGroup.ELITE.value
    if score >= 70:
        return ScannerQualityGroup.HIGH_QUALITY.value
    if score >= 60:
        return ScannerQualityGroup.WATCHLIST.value
    return ScannerQualityGroup.NO_TRADE.value


class SetupQualityService:
    """Deterministic setup quality scorer (0–100)."""

    def score(
        self,
        *,
        trend_strength: float = 0.0,
        structure_score: float = 0.0,
        volume_ratio: float = 1.0,
        momentum_score: float | None = None,
        risk_reward: float = 0.0,
        atr_ok: bool = True,
        session: str | None = None,
        bos_active: bool = False,
        choch_active: bool = False,
        confluence: float = 0.0,
        validation_flags: dict[str, Any] | None = None,
        gates: list[GateCheck] | None = None,
    ) -> SetupQualityResult:
        session_name = session or trading_session()
        flags = validation_flags or {}

        # Trend strength 0–20 from ADX-like input (25–50 → 0–20)
        adx = float(trend_strength or 0.0)
        trend_pts = min(
            float(WEIGHTS["trend_strength"]),
            max(0.0, (adx - 15.0) / 35.0) * WEIGHTS["trend_strength"],
        )

        # Structure 0–20
        base_structure = float(structure_score or 0.0)
        if bos_active:
            base_structure = max(base_structure, 70.0)
        if choch_active:
            base_structure = max(base_structure, base_structure + 10.0)
        if flags.get("structure_sl"):
            base_structure = min(100.0, base_structure + 10.0)
        structure_pts = min(
            float(WEIGHTS["structure"]),
            (base_structure / 100.0) * WEIGHTS["structure"],
        )

        # Liquidity 0–15
        vol = float(volume_ratio or 0.0)
        liquidity_pts = min(
            float(WEIGHTS["liquidity"]),
            max(0.0, min(1.5, vol) / 1.5) * WEIGHTS["liquidity"],
        )
        if flags.get("liquidity") is False:
            liquidity_pts = min(liquidity_pts, 3.0)

        # Momentum 0–15 (ADX + confluence blend)
        mom_src = momentum_score if momentum_score is not None else adx
        mom_pts = min(
            float(WEIGHTS["momentum"]),
            max(0.0, float(mom_src) / 50.0) * WEIGHTS["momentum"] * 0.7
            + (float(confluence) / 100.0) * WEIGHTS["momentum"] * 0.3,
        )

        # Risk reward 0–15
        rr = float(risk_reward or 0.0)
        min_rr = float(settings.MIN_RR)
        preferred = float(settings.PREFERRED_RR)
        if rr <= 0:
            rr_pts = 0.0
        elif rr < min_rr:
            rr_pts = 0.0
        else:
            span = max(0.01, preferred - min_rr)
            rr_pts = min(
                float(WEIGHTS["risk_reward"]),
                ((rr - min_rr) / span) * WEIGHTS["risk_reward"],
            )
            rr_pts = max(rr_pts, WEIGHTS["risk_reward"] * 0.55)  # floor when RR ok

        # Volatility 0–10
        vol_pts = float(WEIGHTS["volatility"]) if atr_ok else 0.0

        # Session 0–5
        if session_name in {"Overlap"}:
            session_pts = float(WEIGHTS["session"])
        elif session_name in {"London", "New York"}:
            session_pts = float(WEIGHTS["session"]) * 0.8
        elif session_name in set(settings.QUAL_ALLOWED_SESSIONS):
            session_pts = float(WEIGHTS["session"]) * 0.4
        else:
            session_pts = 0.0

        components = {
            "trend_strength": round(trend_pts, 2),
            "structure": round(structure_pts, 2),
            "liquidity": round(liquidity_pts, 2),
            "momentum": round(mom_pts, 2),
            "risk_reward": round(rr_pts, 2),
            "volatility": round(vol_pts, 2),
            "session": round(session_pts, 2),
        }
        total = int(round(sum(components.values())))
        total = max(0, min(100, total))

        # Soft penalty if gates failed (should already be NO_TRADE upstream)
        if gates:
            failed = sum(1 for g in gates if g.mandatory and not g.passed)
            if failed:
                total = min(total, 55)

        grade = grade_for_score(total)
        return SetupQualityResult(
            score=total,
            grade=grade.value,
            components=components,
            category=scanner_group_for_score(total),
        )


setup_quality_service = SetupQualityService()
