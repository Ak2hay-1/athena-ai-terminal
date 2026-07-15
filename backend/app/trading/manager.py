"""
Trading Manager.

Coordinates the complete trade execution lifecycle.
"""

from __future__ import annotations

from decimal import Decimal

from app.core.logger import get_logger
from app.schemas.mt5 import (
    MT5OrderRequest,
    MT5OrderResult,
)
from app.services.market_service import MarketService, market_service
from app.services.mt5_service import MT5Service, mt5_service
from app.trading.calculator import TradingCalculator
from app.trading.validators import TradingValidator

logger = get_logger(__name__)


class TradingManager:
    """
    Coordinates trade execution.
    """

    def __init__(
        self,
        mt5: MT5Service | None = None,
        market: MarketService | None = None,
    ) -> None:

        self.mt5 = mt5 or mt5_service

        self.market = market or market_service

        self.validator = TradingValidator()

        self.calculator = TradingCalculator()

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
        request: MT5OrderRequest,
    ) -> None:
        """
        Validate an order before execution.
        """

        self.validator.validate_trade(
            symbol=request.symbol,
            volume=request.volume,
            price=request.price or Decimal("0"),
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )

    # =====================================================
    # Risk
    # =====================================================

    def calculate_required_margin(
        self,
        *,
        volume: Decimal,
        contract_size: Decimal,
        price: Decimal,
        leverage: int,
    ) -> Decimal:
        """
        Estimate required margin.
        """

        return self.calculator.required_margin(
            volume=volume,
            contract_size=contract_size,
            price=price,
            leverage=leverage,
        )

    # =====================================================
    # Execution
    # =====================================================

    def execute_order(
        self,
        request: MT5OrderRequest,
    ) -> MT5OrderResult:
        """
        Execute a validated order.
        """

        logger.info(
            "Executing %s %s %s",
            request.order_type,
            request.volume,
            request.symbol,
        )

        # ----------------------------------------------
        # Validation
        # ----------------------------------------------

        self.validate(request)

        # ----------------------------------------------
        # Execute through MT5
        # ----------------------------------------------

        result = self.mt5.place_order(request)

        logger.info(
            "Trade executed successfully."
        )

        return result

    # =====================================================
    # Close Position
    # =====================================================

    def close_position(
        self,
        ticket: int,
        volume: Decimal | None = None,
    ):
        """
        Close an existing position.
        """

        logger.info(
            "Closing position %s",
            ticket,
        )

        return self.mt5.close_position(
            ticket=ticket,
            volume=volume,
        )

    # =====================================================
    # Modify Position
    # =====================================================

    def modify_position(
        self,
        ticket: int,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
    ):
        """
        Modify SL/TP.
        """

        return self.mt5.modify_position(
            ticket=ticket,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    # =====================================================
    # Cancel Order
    # =====================================================

    def cancel_order(
        self,
        ticket: int,
    ):
        """
        Cancel pending order.
        """

        return self.mt5.cancel_order(
            ticket,
        )

    # =====================================================
    # Positions
    # =====================================================

    def positions(
        self,
    ):
        """
        Get all open positions.
        """

        return self.mt5.positions()

    # =====================================================
    # Orders
    # =====================================================

    def orders(
        self,
    ):
        """
        Get all pending orders.
        """

        return self.mt5.orders()


trading_manager = TradingManager()
