"""
MetaTrader 5 Constants.

Centralized constants and mappings used throughout
the MT5 integration.
"""

from __future__ import annotations

from app.mt5.sdk import mt5

# ==========================================================
# Application
# ==========================================================

DEFAULT_MAGIC_NUMBER = 20260713

DEFAULT_DEVIATION = 20

DEFAULT_TIMEOUT = 60000

DEFAULT_COMMENT = "Athena AI Terminal"

# ==========================================================
# Timeframes
# ==========================================================

TIMEFRAMES: dict[str, int] = {
    "M1": mt5.TIMEFRAME_M1,
    "M2": mt5.TIMEFRAME_M2,
    "M3": mt5.TIMEFRAME_M3,
    "M4": mt5.TIMEFRAME_M4,
    "M5": mt5.TIMEFRAME_M5,
    "M6": mt5.TIMEFRAME_M6,
    "M10": mt5.TIMEFRAME_M10,
    "M12": mt5.TIMEFRAME_M12,
    "M15": mt5.TIMEFRAME_M15,
    "M20": mt5.TIMEFRAME_M20,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H2": mt5.TIMEFRAME_H2,
    "H3": mt5.TIMEFRAME_H3,
    "H4": mt5.TIMEFRAME_H4,
    "H6": mt5.TIMEFRAME_H6,
    "H8": mt5.TIMEFRAME_H8,
    "H12": mt5.TIMEFRAME_H12,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}

# ==========================================================
# Order Types
# ==========================================================

ORDER_TYPES = {
    "BUY": mt5.ORDER_TYPE_BUY,
    "SELL": mt5.ORDER_TYPE_SELL,
    "BUY_LIMIT": mt5.ORDER_TYPE_BUY_LIMIT,
    "SELL_LIMIT": mt5.ORDER_TYPE_SELL_LIMIT,
    "BUY_STOP": mt5.ORDER_TYPE_BUY_STOP,
    "SELL_STOP": mt5.ORDER_TYPE_SELL_STOP,
    "BUY_STOP_LIMIT": mt5.ORDER_TYPE_BUY_STOP_LIMIT,
    "SELL_STOP_LIMIT": mt5.ORDER_TYPE_SELL_STOP_LIMIT,
}

# ==========================================================
# Trade Actions
# ==========================================================

TRADE_ACTIONS = {
    "DEAL": mt5.TRADE_ACTION_DEAL,
    "PENDING": mt5.TRADE_ACTION_PENDING,
    "SLTP": mt5.TRADE_ACTION_SLTP,
    "MODIFY": mt5.TRADE_ACTION_MODIFY,
    "REMOVE": mt5.TRADE_ACTION_REMOVE,
}

# ==========================================================
# Filling Modes
# ==========================================================

FILLING_MODES = {
    "FOK": mt5.ORDER_FILLING_FOK,
    "IOC": mt5.ORDER_FILLING_IOC,
    "RETURN": mt5.ORDER_FILLING_RETURN,
}

# ==========================================================
# Expiration
# ==========================================================

EXPIRATION_TYPES = {
    "GTC": mt5.ORDER_TIME_GTC,
    "DAY": mt5.ORDER_TIME_DAY,
    "SPECIFIED": mt5.ORDER_TIME_SPECIFIED,
    "SPECIFIED_DAY": mt5.ORDER_TIME_SPECIFIED_DAY,
}

# ==========================================================
# Position Types
# ==========================================================

POSITION_TYPES = {
    mt5.POSITION_TYPE_BUY: "BUY",
    mt5.POSITION_TYPE_SELL: "SELL",
}

# ==========================================================
# Tick Flags
# ==========================================================

TICK_FLAGS = {
    mt5.TICK_FLAG_BID: "BID",
    mt5.TICK_FLAG_ASK: "ASK",
    mt5.TICK_FLAG_LAST: "LAST",
    mt5.TICK_FLAG_VOLUME: "VOLUME",
    mt5.TICK_FLAG_BUY: "BUY",
    mt5.TICK_FLAG_SELL: "SELL",
}

# ==========================================================
# Return Codes
# ==========================================================

TRADE_RETCODES = {
    mt5.TRADE_RETCODE_DONE: "Request completed successfully",
    mt5.TRADE_RETCODE_DONE_PARTIAL: "Request partially completed",
    mt5.TRADE_RETCODE_ERROR: "General error",
    mt5.TRADE_RETCODE_REQUOTE: "Requote",
    mt5.TRADE_RETCODE_REJECT: "Request rejected",
    mt5.TRADE_RETCODE_CANCEL: "Request canceled",
    mt5.TRADE_RETCODE_INVALID: "Invalid request",
    mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume",
    mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price",
    mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stop levels",
    mt5.TRADE_RETCODE_NO_MONEY: "Insufficient funds",
    mt5.TRADE_RETCODE_MARKET_CLOSED: "Market closed",
    mt5.TRADE_RETCODE_PRICE_CHANGED: "Price changed",
    mt5.TRADE_RETCODE_PRICE_OFF: "No quotes available",
    mt5.TRADE_RETCODE_TIMEOUT: "Request timeout",
}

# ==========================================================
# Helper Functions
# ==========================================================

def timeframe_to_mt5(timeframe: str) -> int:
    """
    Convert Athena timeframe to MT5 timeframe.
    """

    try:
        return TIMEFRAMES[timeframe.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}"
        ) from exc


def mt5_retcode_message(retcode: int) -> str:
    """
    Convert MT5 return code to readable message.
    """

    return TRADE_RETCODES.get(
        retcode,
        f"Unknown MT5 return code ({retcode})",
    )


def order_type_to_mt5(order_type: str) -> int:
    """
    Convert order type string to MT5 constant.
    """

    try:
        return ORDER_TYPES[order_type.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported order type: {order_type}"
        ) from exc


def filling_mode_to_mt5(mode: str) -> int:
    """
    Convert filling mode to MT5 constant.
    """

    try:
        return FILLING_MODES[mode.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported filling mode: {mode}"
        ) from exc


def expiration_to_mt5(expiration: str) -> int:
    """
    Convert expiration type to MT5 constant.
    """

    try:
        return EXPIRATION_TYPES[expiration.upper()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported expiration type: {expiration}"
        ) from exc