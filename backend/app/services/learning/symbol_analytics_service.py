"""Per-symbol performance analytics."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.learning import RecommendationOutcome
from app.models.learning import SymbolStatistic
from app.models.recommendation import Recommendation
from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import profit_factor
from app.services.learning.metrics_utils import win_rate


class SymbolAnalyticsService:
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
        grouped: dict[str, list] = defaultdict(list)
        for outcome, recommendation in rows:
            grouped[outcome.symbol.upper()].append((outcome, recommendation))

        count = 0
        for symbol, samples in grouped.items():
            labels = [o.label for o, _ in samples]
            rrs = [o.rr for o, _ in samples]
            profits = [
                o.profit if o.profit is not None else o.pnl_proxy for o, _ in samples
            ]
            confidences = [float(r.confidence or 0) for _, r in samples]
            row = (
                self.db.query(SymbolStatistic)
                .filter(SymbolStatistic.symbol == symbol)
                .first()
            )
            if row is None:
                row = SymbolStatistic(symbol=symbol)
                self.db.add(row)
            row.recommendations = len(samples)
            row.win_rate = win_rate(labels)
            row.avg_rr = avg(rrs)
            row.avg_confidence = avg(confidences)
            row.profit_factor = profit_factor(profits)
            count += 1

        self.db.commit()
        return count

    def list_all(self) -> list[SymbolStatistic]:
        return (
            self.db.query(SymbolStatistic)
            .order_by(SymbolStatistic.symbol.asc())
            .all()
        )
