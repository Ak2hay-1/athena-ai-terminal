"""
Session and pattern statistics helpers.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def session_bucket(payload: dict[str, Any]) -> str:
    sessions = payload.get("session") or payload.get("sessions") or []
    if isinstance(sessions, list) and sessions:
        return str(sessions[0])
    return str(payload.get("session_name") or "unknown")


def best_worst_sessions(
    outcomes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    for row in outcomes:
        bucket = session_bucket(row)
        result = str(row.get("outcome") or row.get("result") or "").lower()
        if result in {"win", "tp", "profit", "success"}:
            buckets[bucket].append("win")
        elif result in {"loss", "sl", "fail", "failure"}:
            buckets[bucket].append("loss")

    ranked: list[dict[str, Any]] = []
    for name, results in buckets.items():
        if not results:
            continue
        wins = results.count("win")
        rate = wins / len(results) * 100.0
        ranked.append(
            {
                "session": name,
                "sample_size": len(results),
                "win_rate": round(rate, 2),
            }
        )
    ranked.sort(key=lambda r: r["win_rate"], reverse=True)
    best = ranked[:3]
    worst = list(reversed(ranked[-3:])) if ranked else []
    return best, worst


def repeated_patterns(
    outcomes: list[dict[str, Any]],
    *,
    min_count: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    winners: dict[str, int] = defaultdict(int)
    failures: dict[str, int] = defaultdict(int)
    for row in outcomes:
        key = _pattern_key(row)
        result = str(row.get("outcome") or row.get("result") or "").lower()
        if result in {"win", "tp", "profit", "success"}:
            winners[key] += 1
        elif result in {"loss", "sl", "fail", "failure"}:
            failures[key] += 1

    recurring_winners = [
        {"pattern": k, "count": v}
        for k, v in sorted(winners.items(), key=lambda kv: kv[1], reverse=True)
        if v >= min_count
    ][:10]
    recurring_failures = [
        {"pattern": k, "count": v}
        for k, v in sorted(failures.items(), key=lambda kv: kv[1], reverse=True)
        if v >= min_count
    ][:10]
    return {
        "repeated_winners": recurring_winners,
        "repeated_failures": recurring_failures,
    }


def _pattern_key(row: dict[str, Any]) -> str:
    symbol = str(row.get("symbol") or "?")
    timeframe = str(row.get("timeframe") or "?")
    status = str(row.get("status") or row.get("bias") or "?")
    return f"{symbol}:{timeframe}:{status}"
