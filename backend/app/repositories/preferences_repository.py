"""
User preferences repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_preferences import UserPreferences
from app.repositories.base_repository import BaseRepository


class PreferencesRepository(BaseRepository[UserPreferences]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserPreferences)

    def get_for_user(self, user_id: int) -> UserPreferences | None:
        stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_or_create(self, user_id: int) -> UserPreferences:
        row = self.get_for_user(user_id)
        if row is not None:
            return row
        row = UserPreferences(user_id=user_id)
        self.create(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_all_user_ids(self) -> list[int]:
        stmt = select(UserPreferences.user_id)
        return [int(v) for v in self.db.scalars(stmt).all()]

    def list_auto_trade_enabled(self) -> list[UserPreferences]:
        stmt = (
            select(UserPreferences)
            .where(UserPreferences.auto_trade_enabled.is_(True))
            .order_by(UserPreferences.user_id.asc())
        )
        return list(self.db.scalars(stmt).all())
