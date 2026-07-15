"""
MetaTrader 5 Manager.

Low-level SDK adapter.

This is the ONLY class that communicates directly with the
MetaTrader5 Python SDK.

Responsibilities:
- Authentication
- Account operations
- Market data
- Trading operations
- History operations

This class intentionally contains NO business logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

import MetaTrader5 as mt5

from app.core.logger import get_logger
from app.mt5.constants import timeframe_to_mt5
from app.mt5.exceptions import (
    MT5AccountError,
    MT5CandleError,
    MT5ConnectionError,
    MT5HistoryError,
    MT5LoginError,
    MT5OrderError,
    MT5PositionError,
    MT5SymbolError,
    MT5TickError,
)
from app.mt5.interfaces import IMT5Connection, IMT5Manager

logger = get_logger(__name__)


class MT5Manager(IMT5Manager):
    """
    MetaTrader 5 SDK adapter.
    """

    def __init__(
        self,
        connection: IMT5Connection,
    ) -> None:
        self._connection = connection

    # =====================================================
    # Helpers
    # =====================================================

    def _ensure_connected(self) -> None:
        """
        Ensure the MT5 terminal is initialized and connected.
        """

        if not self._connection.connected:
            raise MT5ConnectionError(
                "MetaTrader 5 terminal is not connected."
            )

    def _call(
        self,
        func: Callable[..., Any],
        *args: Any,
        exception: type[Exception],
        message: str,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an MT5 SDK call with consistent validation.
        """

        self._ensure_connected()

        logger.debug("MT5 SDK call: %s", func.__name__)

        result = func(*args, **kwargs)

        if result is None:
            error = mt5.last_error()

            logger.error(
                "%s | MT5 Error=%s",
                message,
                error,
            )

            raise exception(
                f"{message}. MT5 Error={error}"
            )

        return result

    # =====================================================
    # Authentication
    # =====================================================

    def login(
        self,
        *,
        login: int,
        password: str,
        server: str,
        timeout: int = 60000,
    ) -> bool:
        """
        Login to a trading account.
        """

        self._ensure_connected()

        success = mt5.login(
            login=login,
            password=password,
            server=server,
            timeout=timeout,
        )

        if not success:
            error = mt5.last_error()

            logger.error(
                "MT5 login failed: %s",
                error,
            )

            raise MT5LoginError(
                f"Login failed. MT5 Error={error}"
            )

        logger.info(
            "Logged into MT5 account %s",
            login,
        )

        return True

    # =====================================================
    # Account
    # =====================================================

    def account_info(self):
        return self._call(
            mt5.account_info,
            exception=MT5AccountError,
            message="Unable to retrieve account information",
        )

    # =====================================================
    # Terminal
    # =====================================================

    def terminal_info(self):
        return self._connection.terminal_info()

    def version(self):
        return self._connection.version()

    # =====================================================
    # Symbols
    # =====================================================

    def symbols(self):
        return self._call(
            mt5.symbols_get,
            exception=MT5SymbolError,
            message="Unable to retrieve symbols",
        )

    def symbol_info(
        self,
        symbol: str,
    ):
        return self._call(
            mt5.symbol_info,
            symbol,
            exception=MT5SymbolError,
            message=f"Unknown symbol '{symbol}'",
        )

    def symbol_tick(
        self,
        symbol: str,
    ):
        return self._call(
            mt5.symbol_info_tick,
            symbol,
            exception=MT5TickError,
            message=f"Unable to retrieve tick for '{symbol}'",
        )

    def symbol_select(
        self,
        symbol: str,
        enable: bool = True,
    ) -> bool:
        self._ensure_connected()

        success = mt5.symbol_select(
            symbol,
            enable,
        )

        if not success:
            raise MT5SymbolError(
                f"Unable to select symbol '{symbol}'. "
                f"MT5 Error={mt5.last_error()}"
            )

        return True

    # =====================================================
    # Candles
    # =====================================================

    def copy_rates_from_pos(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int,
        count: int,
    ):
        return self._call(
            mt5.copy_rates_from_pos,
            symbol,
            timeframe_to_mt5(timeframe),
            start,
            count,
            exception=MT5CandleError,
            message="Unable to retrieve candles",
        )

    def copy_rates_range(
        self,
        *,
        symbol: str,
        timeframe: str,
        from_time: datetime,
        to_time: datetime,
    ):
        return self._call(
            mt5.copy_rates_range,
            symbol,
            timeframe_to_mt5(timeframe),
            from_time,
            to_time,
            exception=MT5CandleError,
            message="Unable to retrieve historical candles",
        )

    def copy_ticks_range(
        self,
        *,
        symbol: str,
        from_time: datetime,
        to_time: datetime,
        flags: int = mt5.COPY_TICKS_ALL,
    ):
        return self._call(
            mt5.copy_ticks_range,
            symbol,
            from_time,
            to_time,
            flags,
            exception=MT5TickError,
            message="Unable to retrieve tick history",
        )

    # =====================================================
    # Trading
    # =====================================================

    def order_check(
        self,
        request: dict[str, Any],
    ):
        return self._call(
            mt5.order_check,
            request,
            exception=MT5OrderError,
            message="Order validation failed",
        )

    def order_send(
        self,
        request: dict[str, Any],
    ):
        return self._call(
            mt5.order_send,
            request,
            exception=MT5OrderError,
            message="Order execution failed",
        )

    def positions(
        self,
        *,
        symbol: str | None = None,
    ):
        return self._call(
            mt5.positions_get,
            symbol=symbol,
            exception=MT5PositionError,
            message="Unable to retrieve positions",
        )

    def orders(self):
        return self._call(
            mt5.orders_get,
            exception=MT5OrderError,
            message="Unable to retrieve orders",
        )

    # =====================================================
    # History
    # =====================================================

    def history_orders(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ):
        return self._call(
            mt5.history_orders_get,
            from_time,
            to_time,
            exception=MT5HistoryError,
            message="Unable to retrieve order history",
        )

    def history_deals(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ):
        return self._call(
            mt5.history_deals_get,
            from_time,
            to_time,
            exception=MT5HistoryError,
            message="Unable to retrieve deal history",
        )

