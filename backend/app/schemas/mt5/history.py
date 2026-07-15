"""
MT5 History Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.schemas.mt5.order import MT5OrderType
from app.schemas.mt5.position import MT5PositionType


# ==========================================================
# Deal Type
# ==========================================================

class MT5DealType(str, Enum):
    """
    Deal types.
    """

    BUY = "BUY"

    SELL = "SELL"

    BALANCE = "BALANCE"

    CREDIT = "CREDIT"

    CHARGE = "CHARGE"

    CORRECTION = "CORRECTION"

    BONUS = "BONUS"

    COMMISSION = "COMMISSION"

    COMMISSION_DAILY = "COMMISSION_DAILY"

    COMMISSION_MONTHLY = "COMMISSION_MONTHLY"

    INTEREST = "INTEREST"

    DIVIDEND = "DIVIDEND"

    TAX = "TAX"


# ==========================================================
# Deal Entry
# ==========================================================

class MT5DealEntry(str, Enum):
    """
    Deal entry type.
    """

    IN = "IN"

    OUT = "OUT"

    INOUT = "INOUT"

    OUT_BY = "OUT_BY"


# ==========================================================
# History Request
# ==========================================================

class MT5HistoryRequest(BaseModel):
    """
    Trading history request.
    """

    from_time: datetime

    to_time: datetime

    symbol: str | None = None

    magic: int | None = None


# ==========================================================
# Deal Information
# ==========================================================

class MT5DealInfo(BaseModel):
    """
    Historical deal.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    ticket: int

    order: int

    position: int

    symbol: str

    deal_type: MT5DealType

    entry: MT5DealEntry

    order_type: MT5OrderType

    position_type: MT5PositionType

    volume: Decimal

    price: Decimal

    profit: Decimal

    commission: Decimal

    swap: Decimal

    fee: Decimal

    magic: int

    comment: str

    time: datetime


# ==========================================================
# Order History
# ==========================================================

class MT5OrderHistory(BaseModel):
    """
    Historical order.
    """

    ticket: int

    symbol: str

    order_type: MT5OrderType

    volume: Decimal

    price_open: Decimal

    stop_loss: Decimal

    take_profit: Decimal

    comment: str

    magic: int

    time_setup: datetime

    time_done: datetime | None = None


# ==========================================================
# History Response
# ==========================================================

class MT5HistoryResponse(BaseModel):
    """
    Complete trading history.
    """

    total_deals: int

    total_orders: int

    deals: list[MT5DealInfo]

    orders: list[MT5OrderHistory]


# ==========================================================
# Profit Summary
# ==========================================================

class MT5ProfitSummary(BaseModel):
    """
    Trading summary.
    """

    gross_profit: Decimal

    gross_loss: Decimal

    net_profit: Decimal

    commission: Decimal

    swap: Decimal

    fees: Decimal

    total_volume: Decimal

    total_trades: int

    winning_trades: int

    losing_trades: int

    win_rate: Decimal


# ==========================================================
# Daily Statistics
# ==========================================================

class MT5DailyStatistics(BaseModel):
    """
    Daily performance.
    """

    date: datetime

    profit: Decimal

    trades: int

    wins: int

    losses: int

    volume: Decimal


# ==========================================================
# Monthly Statistics
# ==========================================================

class MT5MonthlyStatistics(BaseModel):
    """
    Monthly performance.
    """

    year: int

    month: int

    profit: Decimal

    trades: int

    wins: int

    losses: int

    volume: Decimal


# ==========================================================
# Equity Point
# ==========================================================

class MT5EquityPoint(BaseModel):
    """
    Equity curve point.
    """

    timestamp: datetime

    equity: Decimal

    balance: Decimal


# ==========================================================
# Equity Curve
# ==========================================================

class MT5EquityCurve(BaseModel):
    """
    Equity curve.
    """

    points: list[MT5EquityPoint]


# ==========================================================
# Trade Analytics
# ==========================================================

class MT5TradeAnalytics(BaseModel):
    """
    Performance analytics.
    """

    total_profit: Decimal

    average_profit: Decimal

    average_loss: Decimal

    largest_profit: Decimal

    largest_loss: Decimal

    expectancy: Decimal

    profit_factor: Decimal

    recovery_factor: Decimal

    sharpe_ratio: Decimal | None = None

    max_drawdown: Decimal

    max_drawdown_percent: Decimal


# ==========================================================
# Export Request
# ==========================================================

class MT5HistoryExportRequest(BaseModel):
    """
    Export history.
    """

    from_time: datetime

    to_time: datetime

    format: str = Field(
        default="csv",
        pattern="^(csv|xlsx|json)$",
    )