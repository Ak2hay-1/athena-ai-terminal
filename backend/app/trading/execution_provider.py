"""
Execution Provider Interface.

Defines the contract for all trade execution providers.
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


class ExecutionProvider(ABC):
    """
    Base execution provider.

    Supported implementations:

    - MT5Execution
    - PaperExecution
    - BacktestExecution
    """

    # =====================================================
    # Lifecycle
    # =====================================================

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the execution backend.
        """
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """
        Disconnect from the execution backend.
        """
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        """
        Check provider health.
        """
        raise NotImplementedError

    # =====================================================
    # Account
    # =====================================================

    @abstractmethod
    def account(self) -> TradeAccount:
        """
        Return trading account information.
        """
        raise NotImplementedError

    # =====================================================
    # Trading
    # =====================================================

    @abstractmethod
    def execute(
        self,
        request: TradeRequest,
    ) -> TradeResult:
        """
        Execute a trade request.
        """
        raise NotImplementedError

    @abstractmethod
    def modify(
        self,
        order: TradeOrder,
    ) -> TradeResult:
        """
        Modify an existing order or position.
        """
        raise NotImplementedError

    @abstractmethod
    def close(
        self,
        ticket: int,
    ) -> TradeResult:
        """
        Close a position.
        """
        raise NotImplementedError

    @abstractmethod
    def cancel(
        self,
        ticket: int,
    ) -> OrderResult:
        """
        Cancel a pending order.
        """
        raise NotImplementedError

    # =====================================================
    # Queries
    # =====================================================

    @abstractmethod
    def positions(self) -> list[TradePosition]:
        """
        Return all open positions.
        """
        raise NotImplementedError

    @abstractmethod
    def orders(self) -> list[TradeOrder]:
        """
        Return all pending orders.
        """
        raise NotImplementedError

    # =====================================================
    # Synchronization
    # =====================================================

    @abstractmethod
    def sync(self) -> None:
        """
        Synchronize local state with broker.
        """
        raise NotImplementedError