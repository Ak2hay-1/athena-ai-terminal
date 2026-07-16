"""
User Watchlist Model.
"""

from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class UserWatchlist(BaseModel):
    """
    User-configured symbol and timeframe pairs to monitor.
    """

    __tablename__ = "user_watchlists"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "symbol",
            "timeframe",
            name="uq_user_watchlist",
        ),
        Index("idx_watchlist_user", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    timeframe: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
