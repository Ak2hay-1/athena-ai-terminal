"""
MetaTrader 5 Execution Provider.
"""

from __future__ import annotations

import MetaTrader5 as mt5

from app.ai.models import AIRecommendation
from app.core.logger import logger
from app.core.settings import settings
from app.trading.execution_provider import ExecutionProvider


class MT5ExecutionProvider(ExecutionProvider):
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

        symbol = recommendation.symbol

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:

            raise RuntimeError(
                f"Unable to obtain tick for {symbol}"
            )

        order_type = (
            mt5.ORDER_TYPE_BUY
            if recommendation.signal == "BUY"
            else mt5.ORDER_TYPE_SELL
        )

        price = (
            tick.ask
            if recommendation.signal == "BUY"
            else tick.bid
        )

        request = {

            "action": mt5.TRADE_ACTION_DEAL,

            "symbol": symbol,

            "volume": self.DEFAULT_VOLUME,

            "type": order_type,

            "price": price,

            "sl": recommendation.stop_loss,

            "tp": recommendation.take_profit,

            "deviation": self.DEFAULT_DEVIATION,

            "magic": self.MAGIC_NUMBER,

            "comment": "Athena",

            "type_time": mt5.ORDER_TIME_GTC,

            "type_filling": mt5.ORDER_FILLING_IOC,

        }

        result = mt5.order_send(request)

        if result is None:

            raise RuntimeError(
                "MT5 returned None."
            )

        if result.retcode != mt5.TRADE_RETCODE_DONE:

            raise RuntimeError(
                f"Order failed: {result.retcode}"
            )

        logger.info(
            "Trade executed. Ticket=%s",
            result.order,
        )

        return {

            "ticket": result.order,

            "retcode": result.retcode,

            "price": price,

        }

    def close(
        self,
        ticket: int,
    ) -> bool:

        positions = mt5.positions_get(
            ticket=ticket,
        )

        if not positions:

            return False

        position = positions[0]

        tick = mt5.symbol_info_tick(
            position.symbol,
        )

        request = {

            "action": mt5.TRADE_ACTION_DEAL,

            "position": ticket,

            "symbol": position.symbol,

            "volume": position.volume,

            "type": (

                mt5.ORDER_TYPE_SELL

                if position.type == mt5.ORDER_TYPE_BUY

                else mt5.ORDER_TYPE_BUY

            ),

            "price": (

                tick.bid

                if position.type == mt5.ORDER_TYPE_BUY

                else tick.ask

            ),

            "deviation": self.DEFAULT_DEVIATION,

            "magic": self.MAGIC_NUMBER,

            "comment": "Athena Close",

            "type_time": mt5.ORDER_TIME_GTC,

            "type_filling": mt5.ORDER_FILLING_IOC,

        }

        result = mt5.order_send(
            request,
        )

        return (

            result is not None

            and

            result.retcode == mt5.TRADE_RETCODE_DONE

        )

    def positions(self) -> list:

        positions = mt5.positions_get()

        if positions is None:

            return []

        return list(
            positions,
        )


mt5_execution = MT5ExecutionProvider()