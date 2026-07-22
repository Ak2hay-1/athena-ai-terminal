"""Structured NO_TRADE / rejection reason builders for API + UI."""

from __future__ import annotations

from typing import Any

from app.qualification.models import GateCheck


def build_rejection_checklist(
    gates: list[GateCheck] | None = None,
    *,
    extra: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Return structured pass/fail checklist for explanation UI.

    Example item:
      {"name": "Trend Strength", "passed": True, "detail": "ADX=32"}
    """
    items: list[dict[str, Any]] = []
    for gate in gates or []:
        items.append(
            {
                "name": gate.name,
                "passed": bool(gate.passed),
                "detail": gate.detail or "",
                "mandatory": bool(gate.mandatory),
            }
        )
    for item in extra or []:
        items.append(
            {
                "name": str(item.get("name") or "Check"),
                "passed": bool(item.get("passed")),
                "detail": str(item.get("detail") or ""),
                "mandatory": bool(item.get("mandatory", True)),
            }
        )
    return items


def format_rejection_summary(checklist: list[dict[str, Any]]) -> list[str]:
    """Human-readable reason lines: '✓ Trend Strong' / '✗ Weak Liquidity'."""
    lines: list[str] = []
    for item in checklist:
        mark = "✓" if item.get("passed") else "✗"
        name = item.get("name") or "Check"
        detail = item.get("detail") or ""
        if detail:
            lines.append(f"{mark} {name}: {detail}")
        else:
            lines.append(f"{mark} {name}")
    return lines


def merge_validation_into_gates(
    flags: dict[str, Any] | None,
    reasons: list[str] | None = None,
) -> list[GateCheck]:
    """Map TradeValidator flags into GateCheck list for unified NO_TRADE UI."""
    flags = flags or {}
    label_map = {
        "trend": "Trend Aligned",
        "bos": "BOS Confirmed",
        "choch": "CHOCH Confirmed",
        "volume": "Volume Support",
        "atr": "ATR Validation",
        "liquidity": "Liquidity / TP",
        "news": "News Filter",
        "structure_sl": "Structure Stop Loss",
        "risk_distance": "Risk Distance",
        "risk_reward": "Risk Reward",
        "spread": "Spread",
        "mtf": "Multi-Timeframe",
        "regime": "Market Regime",
    }
    gates: list[GateCheck] = []
    for key, label in label_map.items():
        if key not in flags:
            continue
        gates.append(
            GateCheck(
                name=label,
                passed=bool(flags[key]),
                detail="",
            )
        )
    # Attach unmatched textual reasons as failed soft gates when no flag match
    if reasons and not gates:
        for reason in reasons:
            gates.append(GateCheck(name="Validation", passed=False, detail=reason))
    return gates
