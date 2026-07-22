"""
Persisted paper trading positions.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class PaperPosition(BaseModel):
    """
    Paper trade row stored in PostgreSQL.
    """

    __tablename__ = "paper_positions"

    __table_args__ = (
        Index("idx_paper_positions_user_status", "user_id", "status"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    ticket: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    signal: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    entry: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    stop_loss: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    take_profit: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    volume: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="OPEN",
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    pnl: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    recommendation_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
    )

    def to_trade_dict(self) -> dict:
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "signal": self.signal,
            "entry": float(self.entry),
            "stop_loss": float(self.stop_loss),
            "take_profit": float(self.take_profit),
            "volume": float(self.volume),
            "status": self.status,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "pnl": float(self.pnl or 0.0),
            "user_id": self.user_id,
        }
