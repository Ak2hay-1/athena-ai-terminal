"""
Outcome labeling for recommendations.

Deprecated thin wrapper — prefer ``OutcomeTracker``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.learning.outcome_tracker import OutcomeTracker


class OutcomeLabeler:
    """Backward-compatible alias for OutcomeTracker."""

    def __init__(self, db: Session) -> None:
        self._tracker = OutcomeTracker(db)

    def label_pending(self) -> int:
        return self._tracker.label_pending()
