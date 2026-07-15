"""
Trading response schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.schemas.trading.enums import (
    OrderStatus,
    TradeStatus,
)


class TradeResult(BaseModel):
    """
    Result of a trade request.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    success: bool

    status: TradeStatus

    message: str

    ticket: int | None = None

    order_ticket: int | None = None

    deal_ticket: int | None = None

    symbol: str

    volume: Decimal

    price: Decimal | None = None

    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
    )


class OrderResult(BaseModel):
    """
    Result of an order query.
    """

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    ticket: int

    status: OrderStatus

    message: str | None = None

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )