"""
MT5 Symbol Schemas.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Symbol Information
# ==========================================================

class MT5SymbolInfo(BaseModel):
    """
    Complete MetaTrader 5 symbol information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    # ------------------------------------------------------
    # Basic
    # ------------------------------------------------------

    name: str

    description: str

    path: str

    currency_base: str

    currency_profit: str

    currency_margin: str

    category: str | None = None

    exchange: str | None = None

    isin: str | None = None

    page: str | None = None

    visible: bool

    select: bool

    custom: bool

    # ------------------------------------------------------
    # Prices
    # ------------------------------------------------------

    bid: Decimal

    ask: Decimal

    last: Decimal

    point: Decimal

    digits: int

    spread: int

    spread_float: bool

    # ------------------------------------------------------
    # Contract
    # ------------------------------------------------------

    contract_size: Decimal

    trade_tick_size: Decimal

    trade_tick_value: Decimal

    trade_tick_value_profit: Decimal

    trade_tick_value_loss: Decimal

    # ------------------------------------------------------
    # Volume
    # ------------------------------------------------------

    volume_min: Decimal

    volume_max: Decimal

    volume_step: Decimal

    volume_limit: Decimal

    # ------------------------------------------------------
    # Margin
    # ------------------------------------------------------

    margin_initial: Decimal

    margin_maintenance: Decimal

    margin_hedged: Decimal

    margin_hedged_use_leg: bool

    # ------------------------------------------------------
    # Swaps
    # ------------------------------------------------------

    swap_long: Decimal

    swap_short: Decimal

    swap_rollover3days: int

    # ------------------------------------------------------
    # Stops
    # ------------------------------------------------------

    trade_stops_level: int

    trade_freeze_level: int

    # ------------------------------------------------------
    # Trading
    # ------------------------------------------------------

    trade_mode: int

    trade_execution: int

    filling_mode: int

    expiration_mode: int

    order_mode: int

    order_gtc_mode: int

    option_mode: int

    option_right: int

    # ------------------------------------------------------
    # Session
    # ------------------------------------------------------

    session_deals: int

    session_buy_orders: int

    session_sell_orders: int

    session_open: Decimal

    session_close: Decimal

    session_aw: Decimal

    session_price_settlement: Decimal

    session_price_limit_min: Decimal

    session_price_limit_max: Decimal

    session_volume: Decimal

    session_turnover: Decimal

    session_interest: Decimal

    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------

    chart_mode: int

    background_color: int

    basis: str | None = None


# ==========================================================
# Symbol Summary
# ==========================================================

class MT5SymbolSummary(BaseModel):
    """
    Lightweight symbol information.
    """

    name: str

    bid: Decimal

    ask: Decimal

    spread: int

    digits: int

    point: Decimal

    trade_mode: int

    visible: bool


# ==========================================================
# Tick Snapshot
# ==========================================================

class MT5Quote(BaseModel):
    """
    Current market quote.
    """

    symbol: str

    bid: Decimal

    ask: Decimal

    last: Decimal

    spread: int

    timestamp: int


# ==========================================================
# Symbol Search
# ==========================================================

class MT5SymbolSearchRequest(BaseModel):
    """
    Search symbols.
    """

    query: str = Field(
        min_length=1,
        max_length=64,
    )


# ==========================================================
# Symbol Selection
# ==========================================================

class MT5SymbolSelectRequest(BaseModel):
    """
    Select or deselect a symbol.
    """

    symbol: str

    enable: bool = True


# ==========================================================
# Symbol Selection Response
# ==========================================================

class MT5SymbolSelectResponse(BaseModel):
    """
    Symbol selection response.
    """

    success: bool

    symbol: str

    message: str


# ==========================================================
# Symbol List
# ==========================================================

class MT5SymbolList(BaseModel):
    """
    Collection of symbols.
    """

    total: int

    symbols: list[MT5SymbolSummary]