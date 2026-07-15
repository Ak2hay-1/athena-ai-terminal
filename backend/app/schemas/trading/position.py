"""
Trading position schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.schemas.trading.enums import (
    PositionSide,
    PositionStatus,
    TradeSource,
)


class TradePosition(BaseModel):
    """
    Unified trading position model.

    Represents an open or closed position regardless
    of the execution provider.
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",
    )

    ticket: int = Field(
        ...,
        description="Broker position ticket.",
    )

    order_ticket: int | None = Field(
        default=None,
        description="Originating order ticket.",
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=32,
    )

    side: PositionSide

    volume: Decimal = Field(
        ...,
        gt=Decimal("0"),
    )

    entry_price: Decimal = Field(
        ...,
        gt=Decimal("0"),
    )

    current_price: Decimal | None = None

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None

    swap: Decimal = Decimal("0")

    commission: Decimal = Decimal("0")

    profit: Decimal = Decimal("0")

    status: PositionStatus = PositionStatus.OPEN

    source: TradeSource = TradeSource.API

    opened_at: datetime

    closed_at: datetime | None = None

    comment: str | None = Field(
        default=None,
        max_length=128,
    )

    magic: int | None = None