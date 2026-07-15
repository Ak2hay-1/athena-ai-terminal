"""
MetaTrader 5 Trading Service.

Provides broker execution operations.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Manager
from app.mt5.mappers import MT5Mapper
from app.schemas.mt5 import (
    MT5OrderRequest,
    MT5OrderResult,
    MT5Position,
)

logger = get_logger(__name__)


class TradingService:
    """
    Broker execution service.

    Responsibilities
    ----------------
    - Market orders
    - Pending orders
    - Position management
    - Order management

    No trading strategy or risk management logic belongs here.
    """

    def __init__(
        self,
        manager: IMT5Manager,
    ) -> None:
        self._manager = manager

    # =====================================================
    # Market Orders
    # =====================================================

    def buy(
        self,
        request: MT5OrderRequest,
    ) -> MT5OrderResult:
        """
        Execute a market buy order.
        """

        logger.info(
            "BUY %s %s",
            request.volume,
            request.symbol,
        )

        result = self._manager.order_send(
            request.model_dump(
                exclude_none=True,
                mode="python",
            )
        )

        return MT5Mapper.order_result(result)

    def sell(
        self,
        request: MT5OrderRequest,
    ) -> MT5OrderResult:
        """
        Execute a market sell order.
        """

        logger.info(
            "SELL %s %s",
            request.volume,
            request.symbol,
        )

        result = self._manager.order_send(
            request.model_dump(
                exclude_none=True,
                mode="python",
            )
        )

        return MT5Mapper.order_result(result)

    # =====================================================
    # Pending Orders
    # =====================================================

    def place_pending(
        self,
        request: MT5OrderRequest,
    ) -> MT5OrderResult:
        """
        Place a pending order.
        """

        logger.info(
            "Pending Order %s",
            request.symbol,
        )

        result = self._manager.order_send(
            request.model_dump(
                exclude_none=True,
                mode="python",
            )
        )

        return MT5Mapper.order_result(result)

    # =====================================================
    # Positions
    # =====================================================

    def positions(
        self,
        symbol: str | None = None,
    ) -> list[MT5Position]:
        """
        Return open positions.
        """

        positions = self._manager.positions(
            symbol=symbol,
        )

        return [
            MT5Mapper.position(position)
            for position in positions
        ]

    # =====================================================
    # Orders
    # =====================================================

    def orders(self):
        """
        Return pending orders.
        """

        orders = self._manager.orders()

        return [
            MT5Mapper.order(order)
            for order in orders
        ]

    # =====================================================
    # Position Management
    # =====================================================

    def modify_position(
        self,
        *,
        ticket: int,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
    ) -> MT5OrderResult:
        """
        Modify an existing position.

        NOTE:
        Uses MT5 TRADE_ACTION_SLTP request.
        """

        raise NotImplementedError

    def close_position(
        self,
        *,
        ticket: int,
        volume: Decimal | None = None,
    ) -> MT5OrderResult:
        """
        Close an existing position.

        NOTE:
        Uses opposite market order internally.
        """

        raise NotImplementedError

    # =====================================================
    # Pending Orders
    # =====================================================

    def cancel_order(
        self,
        ticket: int,
    ) -> MT5OrderResult:
        """
        Cancel a pending order.

        NOTE:
        Uses TRADE_ACTION_REMOVE.
        """

        raise NotImplementedError
