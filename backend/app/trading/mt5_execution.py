"""
MetaTrader 5 Execution Provider.
"""

from __future__ import annotations

import MetaTrader5 as mt5

from app.ai.models import AIRecommendation
from app.core.logger import logger
from app.core.settings import settings


class MT5ExecutionProvider:
    """
    Executes trades on MetaTrader 5.
    """

    MAGIC_NUMBER = 20260712

    DEFAULT_VOLUME = 0.01

    DEFAULT_DEVIATION = 20

    def execute(
        self,
        recommendation: AIRecommendation,
    ) -> dict:

        if recommendation.signal not in ("BUY", "SELL"):
            raise ValueError("Invalid signal for MT5 execution.")

        order_type = (
            mt5.ORDER_TYPE_BUY
            if recommendation.signal == "BUY"
            else mt5.ORDER_TYPE_SELL
        )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": recommendation.symbol,
            "volume": self.DEFAULT_VOLUME,
            "type": order_type,
            "price": recommendation.entry,
            "sl": recommendation.stop_loss,
            "tp": recommendation.take_profit,
            "deviation": self.DEFAULT_DEVIATION,
            "magic": settings.MAGIC_NUMBER,
            "comment": "Athena AI",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            logger.error("MT5 order_send returned None")
            raise RuntimeError("MT5 order failed.")

        return {
            "ticket": result.order,
            "symbol": recommendation.symbol,
            "signal": recommendation.signal,
            "entry": recommendation.entry,
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
            "volume": self.DEFAULT_VOLUME,
            "status": "OPEN",
        }

    def close(
        self,
        ticket: int,
    ) -> bool:

        logger.info("Closing MT5 ticket %s", ticket)
        return True

    def positions(
        self,
    ) -> list:

        positions = mt5.positions_get()

        if positions is None:
            return []

        return [
            {
                "ticket": position.ticket,
                "symbol": position.symbol,
                "signal": "BUY" if position.type == 0 else "SELL",
                "entry": position.price_open,
                "stop_loss": position.sl,
                "take_profit": position.tp,
                "volume": position.volume,
                "status": "OPEN",
            }
            for position in positions
        ]


mt5_execution = MT5ExecutionProvider()
