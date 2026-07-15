"""
Trading interfaces.

Defines infrastructure contracts used by the Trading module.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from app.schemas.trading import (
    OrderResult,
    TradeAccount,
    TradeOrder,
    TradePosition,
    TradeRequest,
    TradeResult,
)


class ITradingBackend(ABC):
    """
    Trading backend interface.

    A backend is responsible for executing trades against
    a broker or simulator.

    Implementations:

    - MT5Service
    - PaperTradingService
    - BacktestTradingService
    """

    # =====================================================
    # Lifecycle
    # =====================================================

    @abstractmethod
    def connect(self) -> bool:
        """Connect to backend."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from backend."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        """Return backend health."""
        raise NotImplementedError

    # =====================================================
    # Account
    # =====================================================

    @abstractmethod
    def account(self) -> TradeAccount:
        """Return account information."""
        raise NotImplementedError

    # =====================================================
    # Trading
    # =====================================================

    @abstractmethod
    def execute(
        self,
        request: TradeRequest,
    ) -> TradeResult:
        """Execute a trade."""
        raise NotImplementedError

    @abstractmethod
    def modify(
        self,
        order: TradeOrder,
    ) -> TradeResult:
        """Modify an existing order."""
        raise NotImplementedError

    @abstractmethod
    def close(
        self,
        ticket: int,
    ) -> TradeResult:
        """Close a position."""
        raise NotImplementedError

    @abstractmethod
    def cancel(
        self,
        ticket: int,
    ) -> OrderResult:
        """Cancel a pending order."""
        raise NotImplementedError

    # =====================================================
    # Queries
    # =====================================================

    @abstractmethod
    def positions(self) -> list[TradePosition]:
        """Return open positions."""
        raise NotImplementedError

    @abstractmethod
    def orders(self) -> list[TradeOrder]:
        """Return pending orders."""
        raise NotImplementedError

    # =====================================================
    # Synchronization
    # =====================================================

    @abstractmethod
    def sync(self) -> None:
        """
        Synchronize broker state.
        """
        raise NotImplementedError