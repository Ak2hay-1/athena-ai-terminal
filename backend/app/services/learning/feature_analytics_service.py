"""Feature performance analytics from checklist + outcomes."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.learning import FeatureStatistic
from app.models.learning import RecommendationOutcome
from app.models.recommendation import Recommendation
from app.services.learning.metrics_utils import FEATURE_KEYS
from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import checklist_passed_names
from app.services.learning.metrics_utils import normalize_feature_name
from app.services.learning.metrics_utils import profit_factor
from app.services.learning.metrics_utils import win_rate


class FeatureAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def refresh(self) -> int:
        rows = (
            self.db.query(RecommendationOutcome, Recommendation)
            .join(
                Recommendation,
                Recommendation.id == RecommendationOutcome.recommendation_id,
            )
            .all()
        )

        buckets: dict[str, list[tuple[str, float | None, float | None]]] = {
            key: [] for key in FEATURE_KEYS
        }

        for outcome, recommendation in rows:
            names = checklist_passed_names(recommendation.institutional_checklist)
            # Also scan analysis for common flags
            analysis = recommendation.analysis or {}
            if analysis.get("bos"):
                names.add("BOS")
            if analysis.get("choch"):
                names.add("CHOCH")
            if analysis.get("fvg") or analysis.get("fair_value_gap"):
                names.add("FVG")

            normalized = {
                normalize_feature_name(name) or name
                for name in names
            }
            for key in FEATURE_KEYS:
                if key in normalized:
                    buckets[key].append(
                        (
                            outcome.label,
                            outcome.rr,
                            outcome.profit if outcome.profit is not None else outcome.pnl_proxy,
                        )
                    )

        upserted = 0
        for key, samples in buckets.items():
            labels = [s[0] for s in samples]
            rrs = [s[1] for s in samples]
            profits = [s[2] for s in samples]
            row = (
                self.db.query(FeatureStatistic)
                .filter(
                    FeatureStatistic.feature_key == key,
                    FeatureStatistic.symbol.is_(None),
                    FeatureStatistic.timeframe.is_(None),
                )
                .first()
            )
            if row is None:
                row = FeatureStatistic(feature_key=key, symbol=None, timeframe=None)
                self.db.add(row)
            row.win_rate = win_rate(labels)
            row.avg_rr = avg(rrs)
            row.sample_size = len(samples)
            row.profit_factor = profit_factor(profits)
            upserted += 1

        self.db.commit()
        return upserted

    def list_all(self) -> list[FeatureStatistic]:
        return (
            self.db.query(FeatureStatistic)
            .order_by(FeatureStatistic.feature_key.asc())
            .all()
        )
