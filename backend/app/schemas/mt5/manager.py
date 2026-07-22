"""
MetaTrader 5 Manager.

High-level wrapper around the MetaTrader5 SDK.

This module should be the ONLY place where MetaTrader5
functions are called directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.mt5.sdk import mt5

from app.core.logger import get_logger
from app.mt5.providers import connection
from app.mt5.constants import (
    expiration_to_mt5,
    filling_mode_to_mt5,
    order_type_to_mt5,
    timeframe_to_mt5,
)
from app.mt5.exceptions import (
    MT5AccountError,
    MT5CandleError,
    MT5ConnectionError,
    MT5HistoryError,
    MT5OrderError,
    MT5PositionError,
    MT5SymbolError,
    MT5TickError,
)

logger = get_logger(__name__)


class MT5Manager:
    """
    High-level MT5 wrapper.
    """

    def __init__(self) -> None:
        self.connection = connection

    # ======================================================
    # Internal
    # ======================================================

    def _ensure_connected(self) -> None:
        """
        Verify terminal connection.
        """

        if not self.connection.connected:
            raise MT5ConnectionError(
                "MetaTrader 5 is not connected."
            )

    # ======================================================
    # Account
    # ======================================================

    def account_info(self):

        self._ensure_connected()

        info = mt5.account_info()

        if info is None:
            raise MT5AccountError(
                "Unable to retrieve account information."
            )

        return info

    def terminal_info(self):

        self._ensure_connected()

        info = mt5.terminal_info()

        if info is None:
            raise MT5ConnectionError(
                "Unable to retrieve terminal information."
            )

        return info

    def version(self):

        self._ensure_connected()

        version = mt5.version()

        if version is None:
            raise MT5ConnectionError(
                "Unable to retrieve terminal version."
            )

        return version

    # ======================================================
    # Symbols
    # ======================================================

    def symbols(self):

        self._ensure_connected()

        symbols = mt5.symbols_get()

        if symbols is None:
            raise MT5SymbolError(
                "Unable to retrieve symbols."
            )

        return symbols

    def symbol_info(
        self,
        symbol: str,
    ):

        self._ensure_connected()

        info = mt5.symbol_info(symbol)

        if info is None:
            raise MT5SymbolError(
                f"Unknown symbol '{symbol}'."
            )

        return info

    def symbol_tick(
        self,
        symbol: str,
    ):

        self._ensure_connected()

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise MT5TickError(
                f"No tick available for '{symbol}'."
            )

        return tick

    def select_symbol(
        self,
        symbol: str,
        enable: bool = True,
    ) -> bool:

        self._ensure_connected()

        return mt5.symbol_select(
            symbol,
            enable,
        )

    # ======================================================
    # Candles
    # ======================================================

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: str,
        start: int,
        count: int,
    ):

        self._ensure_connected()

        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe_to_mt5(timeframe),
            start,
            count,
        )

        if rates is None:
            raise MT5CandleError(
                "Unable to retrieve candle data."
            )

        return rates

    def copy_rates_range(
        self,
        symbol: str,
        timeframe: str,
        from_time: datetime,
        to_time: datetime,
    ):

        self._ensure_connected()

        rates = mt5.copy_rates_range(
            symbol,
            timeframe_to_mt5(timeframe),
            from_time,
            to_time,
        )

        if rates is None:
            raise MT5CandleError(
                "Unable to retrieve historical candles."
            )

        return rates

    # ======================================================
    # Tick History
    # ======================================================

    def copy_ticks_range(
        self,
        symbol: str,
        from_time: datetime,
        to_time: datetime,
        flags: int = mt5.COPY_TICKS_ALL,
    ):

        self._ensure_connected()

        ticks = mt5.copy_ticks_range(
            symbol,
            from_time,
            to_time,
            flags,
        )

        if ticks is None:
            raise MT5HistoryError(
                "Unable to retrieve tick history."
            )

        return ticks

    # ======================================================
    # Orders
    # ======================================================

    def order_send(
        self,
        request: dict[str, Any],
    ):

        self._ensure_connected()

        result = mt5.order_send(request)

        if result is None:
            raise MT5OrderError(
                "Order request failed."
            )

        return result

    def order_check(
        self,
        request: dict[str, Any],
    ):

        self._ensure_connected()

        result = mt5.order_check(request)

        if result is None:
            raise MT5OrderError(
                "Order validation failed."
            )

        return result

    # ======================================================
    # Positions
    # ======================================================

    def positions(
        self,
        symbol: str | None = None,
    ):

        self._ensure_connected()

        if symbol:
            positions = mt5.positions_get(
                symbol=symbol,
            )
        else:
            positions = mt5.positions_get()

        if positions is None:
            raise MT5PositionError(
                "Unable to retrieve positions."
            )

        return positions

    # ======================================================
    # Orders
    # ======================================================

    def orders(self):

        self._ensure_connected()

        orders = mt5.orders_get()

        if orders is None:
            raise MT5OrderError(
                "Unable to retrieve orders."
            )

        return orders

    # ======================================================
    # History
    # ======================================================

    def history_orders(
        self,
        from_time: datetime,
        to_time: datetime,
    ):

        self._ensure_connected()

        orders = mt5.history_orders_get(
            from_time,
            to_time,
        )

        if orders is None:
            raise MT5HistoryError(
                "Unable to retrieve order history."
            )

        return orders

    def history_deals(
        self,
        from_time: datetime,
        to_time: datetime,
    ):

        self._ensure_connected()

        deals = mt5.history_deals_get(
            from_time,
            to_time,
        )

        if deals is None:
            raise MT5HistoryError(
                "Unable to retrieve deal history."
            )

        return deals


manager = MT5Manager()
