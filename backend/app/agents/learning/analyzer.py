"""
Pattern intelligence analyzer — read-only aggregates from memory + learning repo.
"""

from __future__ import annotations

from typing import Any

from app.agents.learning.similarity import cluster_outcomes
from app.agents.learning.similarity import score_bucket_counts
from app.agents.learning.statistics import best_worst_sessions
from app.agents.learning.statistics import repeated_patterns
from app.agents.memory.retrieval import MemoryRetrieval
from app.database.database import SessionLocal
from app.learning.pattern_statistics import PatternStatistics
from app.memory.service import MemoryService


def _memory_outcomes(limit: int = 300) -> list[dict[str, Any]]:
    retrieval = MemoryRetrieval(MemoryService())
    rows = retrieval.query(memory_type="trade_outcome", limit=limit)
    decisions = retrieval.query(memory_type="decision", limit=limit)
    outcomes: list[dict[str, Any]] = []
    for row in rows + decisions:
        payload = dict(row.payload or {})
        payload.setdefault("symbol", row.symbol)
        payload.setdefault("timeframe", row.timeframe)
        outcomes.append(payload)
    return outcomes


def _pattern_win_rates() -> dict[str, float]:
    db = SessionLocal()
    try:
        # Use a representative pair; empty dict if unavailable
        stats = PatternStatistics(db)
        return stats.win_rates("EURUSD", "M5") or {}
    except Exception:
        return {}
    finally:
        db.close()


def analyze_patterns() -> dict[str, Any]:
    outcomes = _memory_outcomes()
    wins = 0
    losses = 0
    rr_values: list[float] = []
    for row in outcomes:
        result = str(row.get("outcome") or row.get("result") or "").lower()
        status = str(row.get("status") or "").upper()
        if result in {"win", "tp", "profit", "success"}:
            wins += 1
        elif result in {"loss", "sl", "fail", "failure"}:
            losses += 1
        elif status == "APPROVED" and "approval" in row:
            # validation decisions without outcome yet
            pass
        rr = row.get("risk_reward") or (row.get("scores") or {}).get("risk_reward")
        if rr is not None:
            try:
                rr_values.append(float(rr))
            except (TypeError, ValueError):
                pass

    sample = wins + losses
    win_rate = (wins / sample * 100.0) if sample else 0.0
    loss_rate = (losses / sample * 100.0) if sample else 0.0
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

    best_sessions, worst_sessions = best_worst_sessions(outcomes)
    patterns = repeated_patterns(outcomes)
    clusters = cluster_outcomes(outcomes)
    buckets = score_bucket_counts(outcomes)
    pattern_rates = _pattern_win_rates()

    return {
        "win_rate": round(win_rate, 2),
        "loss_rate": round(loss_rate, 2),
        "avg_rr": round(avg_rr, 2),
        "sample_size": len(outcomes),
        "labeled_trades": sample,
        "session_stats": {
            "best": best_sessions,
            "worst": worst_sessions,
        },
        "best_sessions": best_sessions,
        "worst_sessions": worst_sessions,
        "recurring_patterns": patterns,
        "similarity_clusters": clusters,
        "confluence_buckets": buckets,
        "strategy_performance": pattern_rates,
        "market_state_performance": buckets,
    }
