"""
Market Tick Model.

Optional raw tick storage (broker/server timestamps) for backtesting
and future machine learning. Populated only when
MARKET_STORE_TICKS is enabled.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class MarketTick(BaseModel):
    """A single normalized market tick."""

    __tablename__ = "market_ticks"

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "time_msc",
            name="uq_market_tick",
        ),
        Index(
            "idx_market_tick_symbol_time",
            "symbol",
            "time",
        ),
    )

    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Broker/server time.
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Broker/server time in epoch milliseconds (dedup key).
    time_msc: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    bid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    ask: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    last: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    spread: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return f"<MarketTick({self.symbol} {self.time_msc})>"
