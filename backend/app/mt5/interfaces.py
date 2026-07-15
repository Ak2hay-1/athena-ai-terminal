"""
MetaTrader 5 Interfaces.

Defines contracts for MT5 infrastructure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Protocol


class IMT5Connection(Protocol):
    """
    MT5 terminal lifecycle.
    """

    @property
    def connected(self) -> bool: ...

    @property
    def initialized(self) -> bool: ...

    def initialize(
        self,
        *,
        path: str | None = None,
        timeout: int = 60000,
        portable: bool = False,
    ) -> bool: ...

    def shutdown(self) -> None: ...

    def terminal_info(self) -> Any: ...

    def version(self) -> tuple[int, int, str]: ...

    def health_check(self) -> bool: ...

    def last_error(self) -> tuple[int, str]: ...


class IMT5Manager(Protocol):
    """
    MT5 SDK adapter.
    """

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
    ) -> bool: ...

    # =====================================================
    # Account
    # =====================================================

    def account_info(self) -> Any: ...

    # =====================================================
    # Terminal
    # =====================================================

    def terminal_info(self) -> Any: ...

    def version(self) -> tuple[int, int, str]: ...

    # =====================================================
    # Market
    # =====================================================

    def symbols(self) -> Any: ...

    def symbol_info(
        self,
        symbol: str,
    ) -> Any: ...

    def symbol_tick(
        self,
        symbol: str,
    ) -> Any: ...

    def symbol_select(
        self,
        symbol: str,
        enable: bool = True,
    ) -> bool: ...

    def copy_rates_from_pos(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int,
        count: int,
    ) -> Any: ...

    def copy_rates_range(
        self,
        *,
        symbol: str,
        timeframe: str,
        from_time: datetime,
        to_time: datetime,
    ) -> Any: ...

    # =====================================================
    # Trading
    # =====================================================

    def order_send(
        self,
        request: dict[str, Any],
    ) -> Any: ...

    def order_check(
        self,
        request: dict[str, Any],
    ) -> Any: ...

    def positions(
        self,
        *,
        symbol: str | None = None,
    ) -> Any: ...

    def orders(self) -> Any: ...

    # =====================================================
    # History
    # =====================================================

    def history_orders(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ) -> Any: ...

    def history_deals(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ) -> Any: ...