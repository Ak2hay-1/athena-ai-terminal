"""
Versioned adaptive confidence weights.

Gradual, clamped updates from feature win-rate lift — no LLM, no random noise.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from datetime import timezone

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models.learning import FeatureStatistic
from app.models.learning import LearningVersion
from app.models.learning import RecommendationOutcome
from app.models.learning import WeightHistory
from app.risk.confidence_engine import ConfidenceEngine
from app.services.learning.metrics_utils import win_rate


# Map confidence factors to institutional feature keys used in analytics.
FACTOR_FEATURE_MAP = {
    "trend": "HTF Trend",
    "smc": "BOS",
    "liquidity": "Liquidity Sweep",
    "volume": "ATR",
    "multi_tf": "HTF Trend",
    "news": "News Filter",
    "risk_quality": "RR",
}


class AdaptiveWeightService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_weights(self) -> dict[str, float]:
        row = (
            self.db.query(WeightHistory)
            .filter(WeightHistory.is_active == 1)
            .order_by(WeightHistory.created_at.desc())
            .first()
        )
        if row and isinstance(row.weights, dict) and row.weights:
            return {k: float(v) for k, v in row.weights.items()}
        return deepcopy(ConfidenceEngine.WEIGHTS)

    def get_active_version(self) -> str:
        row = (
            self.db.query(WeightHistory)
            .filter(WeightHistory.is_active == 1)
            .order_by(WeightHistory.created_at.desc())
            .first()
        )
        return row.version if row else "baseline"

    def list_history(self, limit: int = 50) -> list[WeightHistory]:
        return (
            self.db.query(WeightHistory)
            .order_by(WeightHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_weights(self, *, reason: str = "scheduled") -> WeightHistory | None:
        outcomes = self.db.query(RecommendationOutcome).all()
        if len(outcomes) < settings.LEARNING_WEIGHT_MIN_SAMPLES:
            logger.info(
                "Skipping weight update: samples=%s < min=%s",
                len(outcomes),
                settings.LEARNING_WEIGHT_MIN_SAMPLES,
            )
            return None

        global_wr = win_rate(o.label for o in outcomes) / 100.0
        current = self.get_active_weights()
        baseline = deepcopy(ConfidenceEngine.WEIGHTS)

        # Ensure all baseline keys exist
        for key, value in baseline.items():
            current.setdefault(key, float(value))

        feature_stats = {
            row.feature_key: row
            for row in self.db.query(FeatureStatistic).all()
            if row.symbol is None and row.timeframe is None
        }

        step = float(settings.LEARNING_WEIGHT_STEP)
        max_step = float(settings.LEARNING_WEIGHT_MAX_STEP)
        w_min = float(settings.LEARNING_WEIGHT_MIN)
        w_max = float(settings.LEARNING_WEIGHT_MAX)

        updated = deepcopy(current)
        for factor, feature_key in FACTOR_FEATURE_MAP.items():
            stats = feature_stats.get(feature_key)
            if stats is None or stats.sample_size < settings.LEARNING_ANALYTICS_MIN_SAMPLES:
                continue
            feature_wr = float(stats.win_rate) / 100.0
            lift = feature_wr - global_wr
            delta = max(-max_step, min(max_step, lift * step * 10.0))
            updated[factor] = float(updated.get(factor, baseline[factor])) + delta

        # Clamp then renormalize to 100
        for key in updated:
            updated[key] = max(w_min, min(w_max, float(updated[key])))

        total = sum(updated.values()) or 1.0
        updated = {k: round(v * 100.0 / total, 4) for k, v in updated.items()}

        # Re-clamp after renormalize and fix residual on risk_quality
        for key in updated:
            updated[key] = max(w_min, min(w_max, updated[key]))
        residual = 100.0 - sum(updated.values())
        updated["risk_quality"] = round(
            max(w_min, min(w_max, updated.get("risk_quality", 5.0) + residual)),
            4,
        )

        # Deactivate previous
        active_rows = (
            self.db.query(WeightHistory)
            .filter(WeightHistory.is_active == 1)
            .all()
        )
        for row in active_rows:
            row.is_active = 0

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        learning_version = f"{settings.LEARNING_SYSTEM_VERSION}-{stamp}"
        weight_version = f"w-{stamp}"

        self.db.add(
            LearningVersion(
                version=learning_version,
                notes=f"Adaptive weight update ({reason})",
            )
        )

        history = WeightHistory(
            version=weight_version,
            weights=updated,
            learning_version=learning_version,
            reason=reason,
            is_active=1,
        )
        self.db.add(history)
        self.db.commit()
        logger.info("Published confidence weights version=%s", weight_version)
        return history
