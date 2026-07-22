"""Per-timeframe performance analytics."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.learning import RecommendationOutcome
from app.models.learning import TimeframeStatistic
from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import profit_factor
from app.services.learning.metrics_utils import win_rate


class TimeframeAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def refresh(self) -> int:
        rows = self.db.query(RecommendationOutcome).all()
        grouped: dict[str, list[RecommendationOutcome]] = defaultdict(list)
        for outcome in rows:
            grouped[outcome.timeframe.upper()].append(outcome)

        count = 0
        for timeframe, samples in grouped.items():
            labels = [o.label for o in samples]
            rrs = [o.rr for o in samples]
            profits = [
                o.profit if o.profit is not None else o.pnl_proxy for o in samples
            ]
            row = (
                self.db.query(TimeframeStatistic)
                .filter(TimeframeStatistic.timeframe == timeframe)
                .first()
            )
            if row is None:
                row = TimeframeStatistic(timeframe=timeframe)
                self.db.add(row)
            row.win_rate = win_rate(labels)
            row.avg_rr = avg(rrs)
            row.sample_size = len(samples)
            row.profit_factor = profit_factor(profits)
            row.trade_frequency = float(len(samples))
            count += 1

        self.db.commit()
        return count

    def list_all(self) -> list[TimeframeStatistic]:
        return (
            self.db.query(TimeframeStatistic)
            .order_by(TimeframeStatistic.timeframe.asc())
            .all()
        )
