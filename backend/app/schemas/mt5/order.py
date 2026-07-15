"""
MT5 Order Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Enums
# ==========================================================

class MT5OrderType(str, Enum):
    """
    MT5 order types.
    """

    BUY = "BUY"
    SELL = "SELL"

    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"

    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"

    BUY_STOP_LIMIT = "BUY_STOP_LIMIT"
    SELL_STOP_LIMIT = "SELL_STOP_LIMIT"


class MT5OrderAction(str, Enum):
    """
    Trading actions.
    """

    DEAL = "DEAL"

    PENDING = "PENDING"

    MODIFY = "MODIFY"

    REMOVE = "REMOVE"

    CLOSE = "CLOSE"


class MT5OrderStatus(str, Enum):
    """
    Order status.
    """

    PENDING = "PENDING"

    FILLED = "FILLED"

    PARTIAL = "PARTIAL"

    CANCELED = "CANCELED"

    REJECTED = "REJECTED"

    EXPIRED = "EXPIRED"


class MT5OrderFilling(str, Enum):
    """
    Filling mode.
    """

    FOK = "FOK"

    IOC = "IOC"

    RETURN = "RETURN"


class MT5OrderTime(str, Enum):
    """
    Expiration mode.
    """

    GTC = "GTC"

    DAY = "DAY"

    SPECIFIED = "SPECIFIED"

    SPECIFIED_DAY = "SPECIFIED_DAY"


# ==========================================================
# Request
# ==========================================================

class MT5OrderRequest(BaseModel):
    """
    Create order request.
    """

    symbol: str

    order_type: MT5OrderType

    volume: Decimal = Field(gt=0)

    price: Decimal | None = None

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None

    deviation: int = Field(
        default=20,
        ge=0,
        le=1000,
    )

    filling: MT5OrderFilling = MT5OrderFilling.FOK

    expiration: MT5OrderTime = MT5OrderTime.GTC

    expiration_time: datetime | None = None

    comment: str = Field(
        default="Athena",
        max_length=64,
    )

    magic: int = 20260713


# ==========================================================
# Modify
# ==========================================================

class MT5ModifyOrderRequest(BaseModel):
    """
    Modify order.
    """

    ticket: int

    price: Decimal | None = None

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None

    expiration_time: datetime | None = None


# ==========================================================
# Close
# ==========================================================

class MT5CloseOrderRequest(BaseModel):
    """
    Close position.
    """

    ticket: int

    volume: Decimal | None = None

    comment: str = "Closed by Athena"


# ==========================================================
# Cancel
# ==========================================================

class MT5CancelOrderRequest(BaseModel):
    """
    Cancel pending order.
    """

    ticket: int


# ==========================================================
# Order Information
# ==========================================================

class MT5OrderInfo(BaseModel):
    """
    MT5 order.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    ticket: int

    symbol: str

    order_type: MT5OrderType

    volume: Decimal

    price_open: Decimal

    price_current: Decimal

    stop_loss: Decimal

    take_profit: Decimal

    status: MT5OrderStatus

    magic: int

    comment: str

    time_setup: datetime

    time_done: datetime | None = None


# ==========================================================
# Execution
# ==========================================================

class MT5OrderResult(BaseModel):
    """
    Order execution result.
    """

    success: bool

    ticket: int | None = None

    deal: int | None = None

    order: int | None = None

    volume: Decimal | None = None

    price: Decimal | None = None

    bid: Decimal | None = None

    ask: Decimal | None = None

    retcode: int

    message: str

    request_id: int | None = None

    timestamp: datetime


# ==========================================================
# Validation
# ==========================================================

class MT5OrderValidation(BaseModel):
    """
    Order validation result.
    """

    valid: bool

    errors: list[str] = []

    warnings: list[str] = []


# ==========================================================
# Order List
# ==========================================================

class MT5OrderList(BaseModel):
    """
    Collection of orders.
    """

    total: int

    orders: list[MT5OrderInfo]