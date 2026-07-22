"""
Cluster recurring winners/failures by feature similarity buckets.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.agents.memory.embeddings import build_feature_vector
from app.agents.memory.embeddings import cosine_similarity


def cluster_outcomes(
    outcomes: list[dict[str, Any]],
    *,
    threshold: float = 0.92,
) -> list[dict[str, Any]]:
    """
    Greedy clustering of similar setups; returns clusters with size >= 2.
    """
    if not outcomes:
        return []

    vectors = [build_feature_vector(o) for o in outcomes]
    assigned = [-1] * len(outcomes)
    clusters: list[list[int]] = []

    for i, vec in enumerate(vectors):
        if assigned[i] >= 0:
            continue
        cluster_id = len(clusters)
        members = [i]
        assigned[i] = cluster_id
        for j in range(i + 1, len(vectors)):
            if assigned[j] >= 0:
                continue
            if cosine_similarity(vec, vectors[j]) >= threshold:
                assigned[j] = cluster_id
                members.append(j)
        clusters.append(members)

    result: list[dict[str, Any]] = []
    for members in clusters:
        if len(members) < 2:
            continue
        wins = 0
        losses = 0
        for idx in members:
            outcome = str(
                outcomes[idx].get("outcome") or outcomes[idx].get("result") or ""
            ).lower()
            if outcome in {"win", "tp", "profit", "success"}:
                wins += 1
            elif outcome in {"loss", "sl", "fail", "failure"}:
                losses += 1
        sample = wins + losses
        result.append(
            {
                "size": len(members),
                "win_rate": round((wins / sample * 100.0) if sample else 0.0, 2),
                "label": "recurring_winner" if wins > losses else "recurring_failure",
            }
        )
    result.sort(key=lambda c: c["size"], reverse=True)
    return result[:20]


def score_bucket_counts(outcomes: list[dict[str, Any]]) -> dict[str, int]:
    buckets: dict[str, int] = defaultdict(int)
    for row in outcomes:
        confluence = float(row.get("confluence") or row.get("validation_score") or 0)
        if confluence >= 80:
            buckets["high_confluence"] += 1
        elif confluence >= 60:
            buckets["mid_confluence"] += 1
        else:
            buckets["low_confluence"] += 1
    return dict(buckets)
