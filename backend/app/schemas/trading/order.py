"""
Trading order schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.schemas.trading.enums import (
    FillPolicy,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
    TradeSource,
)


class TradeOrder(BaseModel):
    """
    Unified trading order model.

    This schema represents an order independently of the
    execution provider (MT5, etc.).
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",
    )

    ticket: int | None = Field(
        default=None,
        description="Broker order ticket.",
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=32,
    )

    side: OrderSide

    order_type: OrderType

    volume: Decimal = Field(
        ...,
        gt=Decimal("0"),
    )

    price: Decimal | None = None

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None

    deviation: int = Field(
        default=20,
        ge=0,
    )

    magic: int | None = None

    comment: str | None = Field(
        default=None,
        max_length=128,
    )

    expiration: datetime | None = None

    time_in_force: TimeInForce = TimeInForce.GTC

    fill_policy: FillPolicy = FillPolicy.RETURN

    status: OrderStatus = OrderStatus.PENDING

    source: TradeSource = TradeSource.API

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime | None = None