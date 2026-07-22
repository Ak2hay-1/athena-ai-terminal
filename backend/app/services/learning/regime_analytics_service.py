"""Market regime performance analytics."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.learning import RecommendationOutcome
from app.models.learning import RegimeStatistic
from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import profit_factor
from app.services.learning.metrics_utils import win_rate


class RegimeAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def refresh(self) -> int:
        rows = self.db.query(RecommendationOutcome).all()
        grouped: dict[str, list[RecommendationOutcome]] = defaultdict(list)
        for outcome in rows:
            regime = (outcome.regime or "UNKNOWN").upper()
            grouped[regime].append(outcome)

        count = 0
        for regime, samples in grouped.items():
            labels = [o.label for o in samples]
            rrs = [o.rr for o in samples]
            profits = [
                o.profit if o.profit is not None else o.pnl_proxy for o in samples
            ]
            row = (
                self.db.query(RegimeStatistic)
                .filter(RegimeStatistic.regime == regime)
                .first()
            )
            if row is None:
                row = RegimeStatistic(regime=regime)
                self.db.add(row)
            row.win_rate = win_rate(labels)
            row.avg_rr = avg(rrs)
            row.sample_size = len(samples)
            row.profit_factor = profit_factor(profits)
            count += 1

        self.db.commit()
        return count

    def list_all(self) -> list[RegimeStatistic]:
        return (
            self.db.query(RegimeStatistic)
            .order_by(RegimeStatistic.regime.asc())
            .all()
        )
