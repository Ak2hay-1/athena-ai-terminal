"""
Journal entry repository.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.repositories.base_repository import BaseRepository


class JournalRepository(BaseRepository[JournalEntry]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, JournalEntry)

    def list_for_user(
        self,
        user_id: int,
        *,
        symbol: str | None = None,
        entry_type: str | None = None,
        limit: int = 100,
    ) -> list[JournalEntry]:
        stmt = select(JournalEntry).where(JournalEntry.user_id == user_id)
        if symbol:
            stmt = stmt.where(JournalEntry.symbol == symbol.upper())
        if entry_type:
            stmt = stmt.where(JournalEntry.entry_type == entry_type)
        stmt = stmt.order_by(JournalEntry.created_at.desc()).limit(
            max(1, min(limit, 500))
        )
        return list(self.db.scalars(stmt).all())

    def get_for_user(self, entry_id: int, user_id: int) -> JournalEntry | None:
        stmt = select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == user_id,
        )
        return self.db.scalars(stmt).first()
