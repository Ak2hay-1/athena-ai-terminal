"""
Feature vectors and cosine similarity for trading memory.
"""

from __future__ import annotations

import math
from typing import Any


def build_feature_vector(setup: dict[str, Any]) -> list[float]:
    """
    Deterministic feature vector from structured evidence scores/state.
    """
    scores = setup.get("scores") or {}
    technical = float(
        setup.get("technical_score")
        or scores.get("technical")
        or 0.0
    )
    smc = float(setup.get("smc_score") or scores.get("smc") or 0.0)
    risk = float(
        setup.get("risk_score") or scores.get("risk") or 0.0
    )
    confluence = float(
        setup.get("confluence") or setup.get("validation_score") or 0.0
    )
    rr = float(scores.get("risk_reward") or setup.get("risk_reward") or 0.0)

    symbol = str(setup.get("symbol") or "").upper()
    timeframe = str(setup.get("timeframe") or "").upper()
    status = str(setup.get("status") or "").upper()

    # Simple categorical hashes into [0,1]
    symbol_feat = (sum(ord(c) for c in symbol) % 97) / 97.0
    tf_map = {"M1": 0.1, "M5": 0.2, "M15": 0.3, "M30": 0.4, "H1": 0.5, "H4": 0.7, "D1": 0.9}
    tf_feat = tf_map.get(timeframe, 0.5)
    status_feat = {"APPROVED": 1.0, "WAIT": 0.5, "REJECTED": 0.0}.get(status, 0.3)

    return [
        technical / 100.0,
        smc / 100.0,
        risk / 100.0,
        confluence / 100.0,
        min(rr / 4.0, 1.0),
        symbol_feat,
        tf_feat,
        status_feat,
    ]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a <= 0 or norm_b <= 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_from_memory_payload(payload: dict[str, Any]) -> list[float]:
    if "feature_vector" in payload and isinstance(payload["feature_vector"], list):
        return [float(x) for x in payload["feature_vector"]]
    return build_feature_vector(payload)
