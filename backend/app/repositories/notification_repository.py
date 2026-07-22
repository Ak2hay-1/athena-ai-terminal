"""
Notification delivery repository.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import NotificationDelivery
from app.models.notification import NotificationInteraction
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[NotificationDelivery]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, NotificationDelivery)

    def recent_for_user(
        self,
        user_id: int,
        *,
        limit: int = 50,
    ) -> list[NotificationDelivery]:
        stmt = (
            select(NotificationDelivery)
            .where(NotificationDelivery.user_id == user_id)
            .order_by(NotificationDelivery.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def find_recent_dedupe(
        self,
        user_id: int,
        dedupe_key: str,
        *,
        within_seconds: int,
    ) -> NotificationDelivery | None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
        stmt = (
            select(NotificationDelivery)
            .where(
                NotificationDelivery.user_id == user_id,
                NotificationDelivery.dedupe_key == dedupe_key,
                NotificationDelivery.created_at >= cutoff,
            )
            .order_by(NotificationDelivery.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_for_user(
        self,
        delivery_id: int,
        user_id: int,
    ) -> NotificationDelivery | None:
        stmt = select(NotificationDelivery).where(
            NotificationDelivery.id == delivery_id,
            NotificationDelivery.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def add_interaction(
        self,
        *,
        delivery_id: int,
        user_id: int,
        action: str,
    ) -> NotificationInteraction:
        row = NotificationInteraction(
            delivery_id=delivery_id,
            user_id=user_id,
            action=action,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def interaction_counts(
        self,
        user_id: int,
        *,
        limit: int = 200,
    ) -> list[NotificationInteraction]:
        stmt = (
            select(NotificationInteraction)
            .where(NotificationInteraction.user_id == user_id)
            .order_by(NotificationInteraction.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
