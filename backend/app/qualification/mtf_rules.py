"""Configurable multi-timeframe alignment rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.settings import settings
from app.qualification.models import GateCheck


_TF_RANK = {
    "M1": 1,
    "M5": 2,
    "M15": 3,
    "M30": 4,
    "H1": 5,
    "H4": 6,
    "D1": 7,
    "W1": 8,
}


def required_alignment_timeframes(execution_tf: str) -> list[str]:
    """
    Resolve which higher TFs must agree with the execution timeframe.

    Uses QUAL_MTF_REQUIRED_ALIGNMENT intersected with MULTI_TF_CONTEXT
    for the execution TF so we only require frames that are actually loaded.
    """
    configured = [tf.upper() for tf in (settings.QUAL_MTF_REQUIRED_ALIGNMENT or [])]
    mapping = settings.MULTI_TF_CONTEXT or {}
    linked = {
        str(x).upper()
        for x in (
            mapping.get(execution_tf.upper())
            or mapping.get(execution_tf)
            or []
        )
    }
    exec_u = execution_tf.upper()

    if configured:
        # Prefer configured list, but only TFs higher than execution and
        # present in MULTI_TF_CONTEXT (so M5 doesn't fail for missing H4).
        out: list[str] = []
        for tf in configured:
            if tf == exec_u:
                continue
            if _TF_RANK.get(tf, 0) <= _TF_RANK.get(exec_u, 0):
                continue
            if linked and tf not in linked:
                continue
            out.append(tf)
        if out:
            return out
        # Fall back to linked preferred TFs when configured ones aren't loaded
        preferred = ["H4", "H1", "D1", "M15"]
        return [tf for tf in preferred if tf in linked and tf != exec_u]

    preferred = ["H4", "H1", "D1"]
    return [tf for tf in preferred if tf in linked and tf != exec_u]


def extract_trend_from_frame(dataframe: pd.DataFrame) -> str:
    if dataframe is None or dataframe.empty:
        return "SIDEWAYS"
    if "trend" in dataframe.columns:
        return str(dataframe["trend"].iloc[-1] or "SIDEWAYS").upper()
    # Lightweight proxy: close vs SMA20 if present, else close vs open mid-window
    if "sma_20" in dataframe.columns:
        close = float(dataframe["close"].iloc[-1])
        sma = float(dataframe["sma_20"].iloc[-1] or close)
        if close > sma * 1.0005:
            return "BULLISH"
        if close < sma * 0.9995:
            return "BEARISH"
        return "SIDEWAYS"
    closes = dataframe["close"].astype(float).tail(20)
    if len(closes) < 5:
        return "SIDEWAYS"
    delta = float(closes.iloc[-1] - closes.iloc[0])
    if delta > 0:
        return "BULLISH"
    if delta < 0:
        return "BEARISH"
    return "SIDEWAYS"


def evaluate_mtf_alignment(
    *,
    execution_tf: str,
    execution_trend: str,
    higher_timeframes: dict[str, pd.DataFrame] | None,
    multi_tf_summary: dict[str, Any] | None = None,
) -> tuple[bool, list[GateCheck], list[str]]:
    """
    Strict MTF gate: every required HTF must agree with execution trend.

    When QUAL_MTF_REQUIRE_STRICT is True, disagreement ⇒ fail (NO_TRADE).
    """
    gates: list[GateCheck] = []
    reasons: list[str] = []
    exec_trend = (execution_trend or "SIDEWAYS").upper()

    if not settings.QUAL_MTF_REQUIRE_STRICT:
        gates.append(
            GateCheck(
                name="Multi-Timeframe Alignment",
                passed=True,
                detail="Strict MTF rules disabled",
                mandatory=False,
            )
        )
        return True, gates, reasons

    if exec_trend not in {"BULLISH", "BEARISH"}:
        gates.append(
            GateCheck(
                name="Execution Trend",
                passed=False,
                detail=f"Execution TF {execution_tf} trend is {exec_trend}",
            )
        )
        reasons.append(f"Execution timeframe {execution_tf} is not directional.")
        return False, gates, reasons

    required = required_alignment_timeframes(execution_tf)
    if not required:
        gates.append(
            GateCheck(
                name="Multi-Timeframe Alignment",
                passed=True,
                detail="No required HTF configured",
                mandatory=False,
            )
        )
        return True, gates, reasons

    frames = higher_timeframes or {}
    tf_analyses = ((multi_tf_summary or {}).get("timeframes") or {})
    all_ok = True

    for tf in required:
        tf_u = tf.upper()
        # Skip if required TF is not higher than execution
        if _TF_RANK.get(tf_u, 0) <= _TF_RANK.get(execution_tf.upper(), 0):
            continue

        htf_trend = "SIDEWAYS"
        if tf_u in frames and frames[tf_u] is not None and not frames[tf_u].empty:
            htf_trend = extract_trend_from_frame(frames[tf_u])
        elif tf_u in tf_analyses:
            nested = tf_analyses[tf_u].get("trend") or {}
            if isinstance(nested, dict):
                htf_trend = str(nested.get("direction") or "SIDEWAYS").upper()
            else:
                htf_trend = str(nested or "SIDEWAYS").upper()
        else:
            # Missing HTF data: fail closed when strict
            gates.append(
                GateCheck(
                    name=f"{tf_u} Alignment",
                    passed=False,
                    detail=f"{tf_u} data unavailable",
                )
            )
            reasons.append(f"{tf_u} disagreement (data unavailable).")
            all_ok = False
            continue

        passed = htf_trend == exec_trend
        gates.append(
            GateCheck(
                name=f"{tf_u} Alignment",
                passed=passed,
                detail=f"{tf_u}={htf_trend}, execution={exec_trend}",
            )
        )
        if not passed:
            all_ok = False
            reasons.append(f"{tf_u} disagreement ({htf_trend} vs {exec_trend}).")

    return all_ok, gates, reasons
