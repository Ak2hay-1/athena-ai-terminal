"""
Optional MetaTrader 5 SDK import.

On non-Windows / Docker images the MetaTrader5 package is not installed.
Callers should treat missing SDK operations as unavailable.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:  # pragma: no cover - expected on Linux containers
    def _unavailable(*_args: Any, **_kwargs: Any) -> None:
        return None

    mt5 = SimpleNamespace(  # type: ignore[assignment]
        initialize=_unavailable,
        shutdown=_unavailable,
        login=_unavailable,
        last_error=lambda: (-1, "MetaTrader5 package not installed"),
        terminal_info=_unavailable,
        account_info=_unavailable,
        version=_unavailable,
        symbol_info=_unavailable,
        symbol_info_tick=_unavailable,
        symbol_select=_unavailable,
        copy_rates_from_pos=_unavailable,
        copy_rates_range=_unavailable,
        copy_ticks_from=_unavailable,
        copy_ticks_range=_unavailable,
        positions_get=_unavailable,
        orders_get=_unavailable,
        history_deals_get=_unavailable,
        order_send=_unavailable,
        order_check=_unavailable,
        symbols_get=_unavailable,
        ORDER_TYPE_BUY=0,
        ORDER_TYPE_SELL=1,
        ORDER_TYPE_BUY_LIMIT=2,
        ORDER_TYPE_SELL_LIMIT=3,
        ORDER_TYPE_BUY_STOP=4,
        ORDER_TYPE_SELL_STOP=5,
        ORDER_TYPE_BUY_STOP_LIMIT=6,
        ORDER_TYPE_SELL_STOP_LIMIT=7,
        TRADE_ACTION_DEAL=1,
        TRADE_ACTION_PENDING=5,
        TRADE_ACTION_SLTP=6,
        TRADE_ACTION_MODIFY=7,
        TRADE_ACTION_REMOVE=8,
        ORDER_TIME_GTC=0,
        ORDER_FILLING_IOC=1,
        ORDER_FILLING_FOK=0,
        ORDER_FILLING_RETURN=2,
        POSITION_TYPE_BUY=0,
        POSITION_TYPE_SELL=1,
        TRADE_RETCODE_DONE=10009,
        TRADE_RETCODE_PLACED=10008,
        COPY_TICKS_ALL=-1,
        COPY_TICKS_INFO=1,
        COPY_TICKS_TRADE=2,
        TIMEFRAME_M1=1,
        TIMEFRAME_M5=5,
        TIMEFRAME_M15=15,
        TIMEFRAME_M30=30,
        TIMEFRAME_H1=16385,
        TIMEFRAME_H4=16388,
        TIMEFRAME_D1=16408,
        TIMEFRAME_W1=32769,
        TIMEFRAME_MN1=49153,
    )

__all__ = ["mt5"]
