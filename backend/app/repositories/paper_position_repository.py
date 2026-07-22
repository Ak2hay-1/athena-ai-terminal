"""
Paper position repository.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.paper_position import PaperPosition
from app.repositories.base_repository import BaseRepository


class PaperPositionRepository(BaseRepository[PaperPosition]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PaperPosition)

    def next_ticket(self) -> int:
        value = self.db.scalar(select(func.coalesce(func.max(PaperPosition.ticket), 0)))
        return int(value or 0) + 1

    def list_open(
        self,
        user_id: int | None = None,
    ) -> list[PaperPosition]:
        stmt = select(PaperPosition).where(PaperPosition.status == "OPEN")
        if user_id is not None:
            stmt = stmt.where(PaperPosition.user_id == user_id)
        stmt = stmt.order_by(PaperPosition.ticket.asc())
        return list(self.db.scalars(stmt).all())

    def get_open_by_ticket(
        self,
        ticket: int,
        user_id: int | None = None,
    ) -> PaperPosition | None:
        stmt = select(PaperPosition).where(
            PaperPosition.ticket == ticket,
            PaperPosition.status == "OPEN",
        )
        if user_id is not None:
            stmt = stmt.where(PaperPosition.user_id == user_id)
        return self.db.scalars(stmt).first()

    def count_open(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(PaperPosition)
            .where(
                PaperPosition.user_id == user_id,
                PaperPosition.status == "OPEN",
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def list_closed(
        self,
        user_id: int | None = None,
        *,
        limit: int = 500,
    ) -> list[PaperPosition]:
        stmt = select(PaperPosition).where(PaperPosition.status == "CLOSED")
        if user_id is not None:
            stmt = stmt.where(PaperPosition.user_id == user_id)
        stmt = stmt.order_by(PaperPosition.closed_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_for_user(self, user_id: int) -> list[PaperPosition]:
        stmt = (
            select(PaperPosition)
            .where(PaperPosition.user_id == user_id)
            .order_by(PaperPosition.opened_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def distinct_user_ids(self) -> list[int]:
        stmt = select(PaperPosition.user_id).distinct()
        return [int(v) for v in self.db.scalars(stmt).all()]
