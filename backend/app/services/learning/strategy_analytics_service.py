"""Strategy combination analytics."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.learning import RecommendationOutcome
from app.models.learning import StrategyStatistic
from app.models.recommendation import Recommendation
from app.services.learning.metrics_utils import STRATEGY_COMBOS
from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import checklist_passed_names
from app.services.learning.metrics_utils import normalize_feature_name
from app.services.learning.metrics_utils import profit_factor
from app.services.learning.metrics_utils import win_rate


class StrategyAnalyticsService:
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

        buckets: dict[str, list] = {key: [] for key, _ in STRATEGY_COMBOS}

        for outcome, recommendation in rows:
            names = {
                normalize_feature_name(n) or n
                for n in checklist_passed_names(recommendation.institutional_checklist)
            }
            analysis = recommendation.analysis or {}
            if analysis.get("bos"):
                names.add("BOS")
            if analysis.get("choch"):
                names.add("CHOCH")
            if analysis.get("fvg"):
                names.add("FVG")

            for combo_key, required in STRATEGY_COMBOS:
                if set(required).issubset(names):
                    buckets[combo_key].append(outcome)

        count = 0
        for combo_key, samples in buckets.items():
            labels = [o.label for o in samples]
            rrs = [o.rr for o in samples]
            profits = [
                o.profit if o.profit is not None else o.pnl_proxy for o in samples
            ]
            row = (
                self.db.query(StrategyStatistic)
                .filter(StrategyStatistic.combo_key == combo_key)
                .first()
            )
            if row is None:
                row = StrategyStatistic(combo_key=combo_key)
                self.db.add(row)
            row.win_rate = win_rate(labels)
            row.avg_rr = avg(rrs)
            row.sample_size = len(samples)
            row.profit_factor = profit_factor(profits)
            count += 1

        self.db.commit()
        return count

    def list_all(self) -> list[StrategyStatistic]:
        return (
            self.db.query(StrategyStatistic)
            .order_by(StrategyStatistic.combo_key.asc())
            .all()
        )
