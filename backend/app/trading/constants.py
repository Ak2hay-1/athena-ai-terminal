"""
Trading Engine Constants.

Shared constants used throughout the trading engine.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum


# ==========================================================
# Trade Direction
# ==========================================================

class TradeSide(str, Enum):
    """
    Trade direction.
    """

    BUY = "BUY"
    SELL = "SELL"


# ==========================================================
# Trade Status
# ==========================================================

class TradeStatus(str, Enum):
    """
    Trade lifecycle status.
    """

    PENDING = "PENDING"

    OPEN = "OPEN"

    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"

    CLOSED = "CLOSED"

    CANCELLED = "CANCELLED"

    FAILED = "FAILED"


# ==========================================================
# Order Source
# ==========================================================

class TradeSource(str, Enum):
    """
    Source that created the trade.
    """

    MANUAL = "MANUAL"

    AI = "AI"

    PATTERN_ENGINE = "PATTERN_ENGINE"

    BACKTEST = "BACKTEST"

    API = "API"

    SCHEDULER = "SCHEDULER"


# ==========================================================
# Risk Models
# ==========================================================

class RiskModel(str, Enum):
    """
    Position sizing model.
    """

    FIXED_LOT = "FIXED_LOT"

    FIXED_RISK = "FIXED_RISK"

    PERCENT_BALANCE = "PERCENT_BALANCE"

    PERCENT_EQUITY = "PERCENT_EQUITY"

    KELLY = "KELLY"


# ==========================================================
# Position Sizing
# ==========================================================

class PositionSizingMode(str, Enum):
    """
    Position sizing strategy.
    """

    MANUAL = "MANUAL"

    AUTOMATIC = "AUTOMATIC"


# ==========================================================
# Stop Loss
# ==========================================================

class StopLossMode(str, Enum):
    """
    Stop loss strategy.
    """

    FIXED = "FIXED"

    ATR = "ATR"

    SWING = "SWING"

    VOLATILITY = "VOLATILITY"


# ==========================================================
# Take Profit
# ==========================================================

class TakeProfitMode(str, Enum):
    """
    Take profit strategy.
    """

    FIXED = "FIXED"

    RISK_REWARD = "RISK_REWARD"

    TRAILING = "TRAILING"

    DYNAMIC = "DYNAMIC"


# ==========================================================
# Defaults
# ==========================================================

DEFAULT_MAGIC_NUMBER = 20260713

DEFAULT_SLIPPAGE = 20

DEFAULT_RISK_PERCENT = Decimal("1.00")

DEFAULT_RISK_REWARD = Decimal("2.00")

DEFAULT_MAX_OPEN_TRADES = 10

DEFAULT_MAX_SYMBOL_TRADES = 2

DEFAULT_LOT_SIZE = Decimal("0.01")

DEFAULT_MIN_LOT = Decimal("0.01")

DEFAULT_MAX_LOT = Decimal("100.00")

DEFAULT_LOT_STEP = Decimal("0.01")

DEFAULT_STOPLOSS_POINTS = 100

DEFAULT_TAKEPROFIT_POINTS = 200


# ==========================================================
# Limits
# ==========================================================

MAX_COMMENT_LENGTH = 64

MAX_PENDING_ORDERS = 100

MAX_SLIPPAGE = 1000

MAX_DEVIATION = 1000


# ==========================================================
# Validation
# ==========================================================

SUPPORTED_TIMEFRAMES = (
    "M1",
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
)

SUPPORTED_ORDER_TYPES = (
    "BUY",
    "SELL",
    "BUY_LIMIT",
    "SELL_LIMIT",
    "BUY_STOP",
    "SELL_STOP",
)

SUPPORTED_FILLING_TYPES = (
    "FOK",
    "IOC",
    "RETURN",
)