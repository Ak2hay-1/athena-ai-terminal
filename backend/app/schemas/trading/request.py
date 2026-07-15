"""
Trading request schemas.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.schemas.trading.enums import (
    ExecutionMode,
    OrderSide,
    OrderType,
    TimeInForce,
    FillPolicy,
    TradeSource,
)


class TradeRequest(BaseModel):
    """
    Request to create a new trade.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=32,
    )

    side: OrderSide

    order_type: OrderType = OrderType.MARKET

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

    time_in_force: TimeInForce = TimeInForce.GTC

    fill_policy: FillPolicy = FillPolicy.RETURN

    execution_mode: ExecutionMode = ExecutionMode.MT5_DEMO

    source: TradeSource = TradeSource.API


class TradeUpdateRequest(BaseModel):
    """
    Update an existing position.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    ticket: int

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None

    comment: str | None = None


class ClosePositionRequest(BaseModel):
    """
    Close an existing position.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    ticket: int

    volume: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
    )


class CancelOrderRequest(BaseModel):
    """
    Cancel a pending order.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    ticket: int