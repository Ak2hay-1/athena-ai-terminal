"""
Trading enumerations.

Shared enumerations used across the Trading module.
"""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    """
    Trade execution mode.
    """

    PAPER = "paper"
    MT5_DEMO = "mt5_demo"
    MT5_LIVE = "mt5_live"


class OrderSide(str, Enum):
    """
    Trade direction.
    """

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """
    Supported order types.
    """

    MARKET = "market"

    LIMIT = "limit"

    STOP = "stop"

    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """
    Order lifecycle status.
    """

    PENDING = "pending"

    FILLED = "filled"

    PARTIALLY_FILLED = "partially_filled"

    CANCELLED = "cancelled"

    REJECTED = "rejected"

    EXPIRED = "expired"


class PositionSide(str, Enum):
    """
    Position direction.
    """

    LONG = "long"

    SHORT = "short"


class PositionStatus(str, Enum):
    """
    Position lifecycle.
    """

    OPEN = "open"

    CLOSED = "closed"


class TradeStatus(str, Enum):
    """
    Trade execution status.
    """

    SUCCESS = "success"

    FAILED = "failed"

    REJECTED = "rejected"

    CANCELLED = "cancelled"


class TimeInForce(str, Enum):
    """
    Order validity.
    """

    GTC = "gtc"

    DAY = "day"

    IOC = "ioc"

    FOK = "fok"


class FillPolicy(str, Enum):
    """
    Order fill policy.
    """

    RETURN = "return"

    IOC = "ioc"

    FOK = "fok"


class TradeSource(str, Enum):
    """
    Source that created the trade.
    """

    MANUAL = "manual"

    API = "api"

    AI = "ai"

    STRATEGY = "strategy"

    BACKTEST = "backtest"

    COPY_TRADING = "copy_trading"


class ExecutionStatus(str, Enum):
    """
    Broker connection status.
    """

    CONNECTED = "connected"

    DISCONNECTED = "disconnected"

    RECONNECTING = "reconnecting"

    ERROR = "error"