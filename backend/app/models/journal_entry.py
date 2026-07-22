"""
Persisted trading journal entries.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class JournalEntry(BaseModel):
    """
    User-scoped journal note / trade or recommendation review.
    """

    __tablename__ = "journal_entries"

    __table_args__ = (
        Index("idx_journal_entries_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    entry_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="note",
    )

    recommendation_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )

    paper_position_id: Mapped[int | None] = mapped_column(
        ForeignKey("paper_positions.id", ondelete="SET NULL"),
        nullable=True,
    )

    symbol: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    tags: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
