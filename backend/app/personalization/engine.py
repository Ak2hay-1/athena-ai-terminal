"""
Personalization engine — notification relevance.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.database.database import SessionLocal
from app.personalization.scoring import score_message
from app.personalization.scoring import should_notify_by_score
from app.repositories.preferences_repository import PreferencesRepository


class PersonalizationEngine:
    def should_notify(
        self,
        user_id: int,
        message: dict[str, Any],
        *,
        db: Session | None = None,
    ) -> bool:
        if not settings.PERSONALIZATION_ENABLED:
            return True
        own_session = db is None
        session = db or SessionLocal()
        try:
            prefs = PreferencesRepository(session).get_or_create(user_id)
            score = score_message(
                message,
                preferred_assets=list(prefs.favorite_assets or []),
                ignored_symbols=list(prefs.ignored_symbols or []),
                preferred_rr=prefs.preferred_rr,
                preferred_sessions=list(prefs.preferred_sessions or []),
                soft_weights=dict(prefs.soft_weights or {}),
            )
            # Critical always passes
            if str(message.get("priority") or "").lower() == "critical":
                return True
            return should_notify_by_score(
                score,
                frequency=prefs.notification_frequency or "normal",
            )
        finally:
            if own_session:
                session.close()

    def relevance_score(
        self,
        user_id: int,
        message: dict[str, Any],
        *,
        db: Session | None = None,
    ) -> float:
        own_session = db is None
        session = db or SessionLocal()
        try:
            prefs = PreferencesRepository(session).get_or_create(user_id)
            return score_message(
                message,
                preferred_assets=list(prefs.favorite_assets or []),
                ignored_symbols=list(prefs.ignored_symbols or []),
                preferred_rr=prefs.preferred_rr,
                preferred_sessions=list(prefs.preferred_sessions or []),
                soft_weights=dict(prefs.soft_weights or {}),
            )
        finally:
            if own_session:
                session.close()


personalization_engine = PersonalizationEngine()
