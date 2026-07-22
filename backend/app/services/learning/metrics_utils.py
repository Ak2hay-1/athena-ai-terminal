"""Shared deterministic metrics helpers for learning analytics."""

from __future__ import annotations

from typing import Iterable


def win_rate(labels: Iterable[str]) -> float:
    values = list(labels)
    if not values:
        return 0.0
    wins = sum(1 for label in values if label == "WIN")
    return round(100.0 * wins / len(values), 2)


def avg(values: Iterable[float | None]) -> float:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return 0.0
    return round(sum(nums) / len(nums), 4)


def profit_factor(profits: Iterable[float | None]) -> float:
    gains = 0.0
    losses = 0.0
    for profit in profits:
        if profit is None:
            continue
        value = float(profit)
        if value > 0:
            gains += value
        elif value < 0:
            losses += abs(value)
    if losses <= 0:
        return round(gains, 4) if gains > 0 else 0.0
    return round(gains / losses, 4)


FEATURE_KEYS = (
    "BOS",
    "CHOCH",
    "Order Block",
    "Liquidity Sweep",
    "FVG",
    "HTF Trend",
    "ATR",
    "RR",
    "News Filter",
)

STRATEGY_COMBOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("BOS+FVG", ("BOS", "FVG")),
    ("BOS+Order Block", ("BOS", "Order Block")),
    ("Liquidity Sweep+CHOCH", ("Liquidity Sweep", "CHOCH")),
    ("HTF Trend+Pullback", ("HTF Trend", "Order Block")),
    ("BOS+Liquidity+Order Block", ("BOS", "Liquidity Sweep", "Order Block")),
)

CONFIDENCE_BUCKETS: tuple[tuple[str, int, int, float], ...] = (
    ("0-50", 0, 50, 25.0),
    ("50-60", 50, 60, 55.0),
    ("60-70", 60, 70, 65.0),
    ("70-80", 70, 80, 75.0),
    ("80-90", 80, 90, 85.0),
    ("90-100", 90, 101, 95.0),
)


def checklist_passed_names(checklist: list | dict | None) -> set[str]:
    names: set[str] = set()
    if isinstance(checklist, list):
        for item in checklist:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("item") or "").strip()
            passed = item.get("passed")
            if name and passed:
                names.add(name)
    elif isinstance(checklist, dict):
        for key, value in checklist.items():
            if value is True or (isinstance(value, dict) and value.get("passed")):
                names.add(str(key))
    return names


def normalize_feature_name(name: str) -> str | None:
    key = name.strip().lower()
    mapping = {
        "bos": "BOS",
        "choch": "CHOCH",
        "order block": "Order Block",
        "liquidity sweep": "Liquidity Sweep",
        "fvg": "FVG",
        "htf trend": "HTF Trend",
        "atr": "ATR",
        "rr": "RR",
        "news filter": "News Filter",
        "news": "News Filter",
    }
    return mapping.get(key)
