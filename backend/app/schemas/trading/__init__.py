"""
Trading schemas.

This package contains all request, response and domain models
used by the Trading module.

Modules
-------
enums
    Trading enumerations.

account
    Trading account schemas.

order
    Order schemas.

position
    Position schemas.

request
    Trading request schemas.

response
    Trading response schemas.

execution
    Execution result schemas.
"""

from app.schemas.trading.account import TradingAccount
from app.schemas.trading.enums import (
    ExecutionMode,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionStatus,
    TradeStatus,
)
from app.schemas.trading.execution import ExecutionResult
from app.schemas.trading.order import Order
from app.schemas.trading.position import Position
from app.schemas.trading.request import (
    CancelOrderRequest,
    ClosePositionRequest,
    ModifyPositionRequest,
    TradeRequest,
)
from app.schemas.trading.response import (
    OrderResult,
    TradeResult,
)

__all__ = [
    # Enums
    "ExecutionMode",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "PositionStatus",
    "TradeStatus",

    # Models
    "TradingAccount",
    "Order",
    "Position",

    # Requests
    "TradeRequest",
    "ModifyPositionRequest",
    "ClosePositionRequest",
    "CancelOrderRequest",

    # Responses
    "TradeResult",
    "OrderResult",
    "ExecutionResult",
]