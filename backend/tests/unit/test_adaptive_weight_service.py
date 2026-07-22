"""Adaptive confidence weight update tests."""

from __future__ import annotations

from app.risk.confidence_engine import ConfidenceEngine
from app.services.learning.adaptive_weight_service import AdaptiveWeightService
from app.services.learning.metrics_utils import win_rate


class _FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)

    def limit(self, n):
        return self


class _FakeDB:
    def __init__(self, outcomes, features):
        self.outcomes = outcomes
        self.features = features
        self.added = []
        self.committed = False

    def query(self, model):
        name = getattr(model, "__name__", str(model))
        if "RecommendationOutcome" in name or name.endswith("RecommendationOutcome"):
            return _FakeQuery(self.outcomes)
        if "FeatureStatistic" in name:
            return _FakeQuery(self.features)
        if "WeightHistory" in name:
            return _FakeQuery([])
        if "LearningVersion" in name:
            return _FakeQuery([])
        return _FakeQuery([])

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True


def test_win_rate_helper():
    assert win_rate(["WIN", "LOSS", "WIN", "WIN"]) == 75.0


def test_confidence_engine_uses_injected_weights():
    engine = ConfidenceEngine({"trend": 40, "smc": 10, "liquidity": 10, "volume": 10, "multi_tf": 10, "news": 10, "risk_quality": 10})
    assert engine.weights["trend"] == 40
    assert ConfidenceEngine.WEIGHTS["trend"] == 20


def test_update_weights_skips_insufficient_samples(monkeypatch):
    from app.services.learning import adaptive_weight_service as mod

    monkeypatch.setattr(mod.settings, "LEARNING_WEIGHT_MIN_SAMPLES", 50)
    db = _FakeDB(outcomes=[object()] * 10, features=[])
    service = AdaptiveWeightService(db)
    assert service.update_weights() is None
