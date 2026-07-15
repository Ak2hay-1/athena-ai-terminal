"""
MetaTrader 5 History Service.

Provides historical trading data.
"""

from __future__ import annotations

from datetime import datetime

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Manager
from app.mt5.mappers import MT5Mapper
from app.schemas.mt5 import (
    MT5Deal,
    MT5HistoryOrder,
)

logger = get_logger(__name__)


class HistoryService:
    """
    MT5 history service.

    Responsibilities
    ----------------
    - Historical orders
    - Historical deals

    This service is read-only.
    """

    def __init__(
        self,
        manager: IMT5Manager,
    ) -> None:
        self._manager = manager

    # =====================================================
    # Orders
    # =====================================================

    def get_orders(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ) -> list[MT5HistoryOrder]:
        """
        Return historical orders.
        """

        logger.debug(
            "Loading order history."
        )

        orders = self._manager.history_orders(
            from_time=from_time,
            to_time=to_time,
        )

        return [
            MT5Mapper.history_order(order)
            for order in orders
        ]

    # =====================================================
    # Deals
    # =====================================================

    def get_deals(
        self,
        *,
        from_time: datetime,
        to_time: datetime,
    ) -> list[MT5Deal]:
        """
        Return historical deals.
        """

        logger.debug(
            "Loading deal history."
        )

        deals = self._manager.history_deals(
            from_time=from_time,
            to_time=to_time,
        )

        return [
            MT5Mapper.history_deal(deal)
            for deal in deals
        ]
