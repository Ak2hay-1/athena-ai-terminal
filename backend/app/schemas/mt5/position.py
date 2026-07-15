"""
MT5 Position Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Position Type
# ==========================================================

class MT5PositionType(str, Enum):
    """
    MT5 position types.
    """

    BUY = "BUY"
    SELL = "SELL"


# ==========================================================
# Position Information
# ==========================================================

class MT5PositionInfo(BaseModel):
    """
    Open trading position.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    ticket: int

    symbol: str

    position_type: MT5PositionType

    volume: Decimal

    price_open: Decimal

    price_current: Decimal

    stop_loss: Decimal

    take_profit: Decimal

    profit: Decimal

    swap: Decimal

    commission: Decimal

    magic: int

    comment: str

    time_open: datetime

    identifier: int


# ==========================================================
# Position Summary
# ==========================================================

class MT5PositionSummary(BaseModel):
    """
    Lightweight position.
    """

    ticket: int

    symbol: str

    position_type: MT5PositionType

    volume: Decimal

    profit: Decimal


# ==========================================================
# Position List
# ==========================================================

class MT5PositionList(BaseModel):
    """
    Collection of positions.
    """

    total: int

    positions: list[MT5PositionInfo]


# ==========================================================
# Modify Position
# ==========================================================

class MT5ModifyPositionRequest(BaseModel):
    """
    Modify SL / TP.
    """

    ticket: int

    stop_loss: Decimal | None = None

    take_profit: Decimal | None = None


# ==========================================================
# Partial Close
# ==========================================================

class MT5PartialCloseRequest(BaseModel):
    """
    Partially close a position.
    """

    ticket: int

    volume: Decimal = Field(
        gt=0,
    )


# ==========================================================
# Close Position
# ==========================================================

class MT5ClosePositionRequest(BaseModel):
    """
    Close entire position.
    """

    ticket: int

    comment: str = "Closed by Athena"


# ==========================================================
# Position Result
# ==========================================================

class MT5PositionResult(BaseModel):
    """
    Position operation result.
    """

    success: bool

    ticket: int

    message: str

    timestamp: datetime


# ==========================================================
# Position Statistics
# ==========================================================

class MT5PositionStatistics(BaseModel):
    """
    Current portfolio statistics.
    """

    total_positions: int

    buy_positions: int

    sell_positions: int

    total_volume: Decimal

    floating_profit: Decimal

    total_swap: Decimal

    total_commission: Decimal

    largest_profit: Decimal

    largest_loss: Decimal


# ==========================================================
# Position Filter
# ==========================================================

class MT5PositionFilter(BaseModel):
    """
    Filter open positions.
    """

    symbol: str | None = None

    magic: int | None = None

    position_type: MT5PositionType | None = None


# ==========================================================
# Risk Metrics
# ==========================================================

class MT5PositionRisk(BaseModel):
    """
    Position risk metrics.
    """

    ticket: int

    symbol: str

    risk_amount: Decimal

    reward_amount: Decimal

    risk_reward_ratio: Decimal

    stop_distance: Decimal

    take_profit_distance: Decimal