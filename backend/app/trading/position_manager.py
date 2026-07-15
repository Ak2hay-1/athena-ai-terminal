"""
Athena Position Manager.

Responsible for monitoring and managing open positions.
"""

from __future__ import annotations

from app.core.logger import logger
from app.trading.order_manager import order_manager


class PositionManager:
    """
    Position lifecycle management.

    Features:
    - List open positions
    - Close position
    - Close all positions
    - Move SL to breakeven (future)
    - Trailing stop (future)
    - Partial close (future)
    """

    def get_open_positions(self) -> list:
        """
        Return all open positions.
        """
        return order_manager.positions()

    def close_position(
        self,
        ticket: int,
    ) -> bool:
        """
        Close a single position.
        """
        success = order_manager.close(ticket)

        if success:
            logger.info(
                "Position %s closed.",
                ticket,
            )
        else:
            logger.warning(
                "Failed to close %s",
                ticket,
            )

        return success

    def close_all(self) -> int:
        """
        Close every open position.
        """

        positions = self.get_open_positions()

        closed = 0

        for position in positions:

            ticket = position.get(
                "ticket",
                None,
            )

            if ticket is None:
                continue

            if self.close_position(ticket):

                closed += 1

        logger.info(
            "%d positions closed.",
            closed,
        )

        return closed

    # -----------------------------------------------------
    # Future Features
    # -----------------------------------------------------

    def move_to_break_even(
        self,
        ticket: int,
    ) -> bool:
        """
        Placeholder for break-even logic.
        """
        logger.info(
            "Break-even not implemented for %s",
            ticket,
        )
        return False

    def trail_stop(
        self,
        ticket: int,
    ) -> bool:
        """
        Placeholder for trailing stop logic.
        """
        logger.info(
            "Trailing stop not implemented for %s",
            ticket,
        )
        return False


position_manager = PositionManager()