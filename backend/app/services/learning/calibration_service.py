"""Confidence calibration buckets vs actual win rate."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.learning import ConfidenceCalibration
from app.models.learning import RecommendationOutcome
from app.services.learning.metrics_utils import CONFIDENCE_BUCKETS
from app.services.learning.metrics_utils import win_rate


class CalibrationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def refresh(self) -> int:
        rows = self.db.query(RecommendationOutcome).all()
        buckets: dict[str, list[str]] = {name: [] for name, *_ in CONFIDENCE_BUCKETS}

        for outcome in rows:
            confidence = outcome.confidence_at_entry
            if confidence is None:
                continue
            for name, low, high, _mid in CONFIDENCE_BUCKETS:
                if low <= int(confidence) < high:
                    buckets[name].append(outcome.label)
                    break

        count = 0
        for name, low, high, mid in CONFIDENCE_BUCKETS:
            labels = buckets[name]
            row = (
                self.db.query(ConfidenceCalibration)
                .filter(ConfidenceCalibration.bucket == name)
                .first()
            )
            if row is None:
                row = ConfidenceCalibration(bucket=name)
                self.db.add(row)
            row.predicted_mid = mid
            row.actual_win_rate = win_rate(labels)
            row.sample_size = len(labels)
            count += 1

        self.db.commit()
        return count

    def list_all(self) -> list[ConfidenceCalibration]:
        return (
            self.db.query(ConfidenceCalibration)
            .order_by(ConfidenceCalibration.bucket.asc())
            .all()
        )
