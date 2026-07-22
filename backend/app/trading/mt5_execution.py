"""
MetaTrader 5 Execution Provider.
"""

from __future__ import annotations

from app.ai.models import AIRecommendation
from app.core.logger import logger
from app.core.settings import settings
from app.mt5.sdk import mt5

# TRADE_RETCODE_DONE / TRADE_RETCODE_PLACED
_SUCCESS_RETCODES = frozenset({10009, 10008})


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
        *,
        volume: float | None = None,
    ) -> dict:
        signal = recommendation.signal
        if hasattr(signal, "value"):
            signal = signal.value
        signal = str(signal).upper()

        if signal not in ("BUY", "SELL"):
            raise ValueError("Invalid signal for MT5 execution.")

        entry = float(recommendation.entry or 0)
        stop_loss = float(recommendation.stop_loss or 0)
        take_profit = float(recommendation.take_profit or 0)
        if not entry or not stop_loss or not take_profit:
            raise ValueError("Entry, stop loss, and take profit are required.")

        lot = float(volume) if volume and volume > 0 else self.DEFAULT_VOLUME
        symbol = recommendation.symbol

        if hasattr(mt5, "symbol_select"):
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error("MT5 symbol_info_tick returned None for %s", symbol)
            raise RuntimeError("MT5 tick unavailable.")

        ask = float(tick.ask)
        bid = float(tick.bid)

        use_limit = False
        if signal == "BUY":
            if entry < ask:
                use_limit = True
                order_type = getattr(mt5, "ORDER_TYPE_BUY_LIMIT", 2)
                price = entry
            else:
                order_type = getattr(mt5, "ORDER_TYPE_BUY", 0)
                price = ask
        else:
            if entry > bid:
                use_limit = True
                order_type = getattr(mt5, "ORDER_TYPE_SELL_LIMIT", 3)
                price = entry
            else:
                order_type = getattr(mt5, "ORDER_TYPE_SELL", 1)
                price = bid

        if use_limit:
            request = {
                "action": getattr(mt5, "TRADE_ACTION_PENDING", 5),
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": self.DEFAULT_DEVIATION,
                "magic": getattr(settings, "MAGIC_NUMBER", self.MAGIC_NUMBER),
                "comment": "Athena AI",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": getattr(mt5, "ORDER_FILLING_RETURN", 2),
            }
            order_kind = "LIMIT"
            status = "PENDING"
        else:
            request = {
                "action": getattr(mt5, "TRADE_ACTION_DEAL", 1),
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": self.DEFAULT_DEVIATION,
                "magic": getattr(settings, "MAGIC_NUMBER", self.MAGIC_NUMBER),
                "comment": "Athena AI",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": getattr(mt5, "ORDER_FILLING_IOC", 1),
            }
            order_kind = "MARKET"
            status = "OPEN"

        result = mt5.order_send(request)

        if result is None:
            logger.error("MT5 order_send returned None")
            raise RuntimeError("MT5 order failed.")

        retcode = getattr(result, "retcode", None)
        if retcode is not None and retcode not in _SUCCESS_RETCODES:
            logger.error(
                "MT5 order rejected retcode=%s comment=%s",
                retcode,
                getattr(result, "comment", ""),
            )
            raise RuntimeError(
                f"MT5 order rejected: {getattr(result, 'comment', retcode)}"
            )

        fill_price = float(
            getattr(result, "price", 0) or price or entry
        )
        return {
            "ticket": int(getattr(result, "order", 0) or getattr(result, "deal", 0) or 0),
            "symbol": symbol,
            "signal": signal,
            "entry": fill_price if order_kind == "MARKET" else entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "volume": lot,
            "status": status,
            "order_type": order_kind,
        }

    def close(
        self,
        ticket: int,
    ) -> bool:
        positions = mt5.positions_get(ticket=ticket)
        if positions:
            position = positions[0]
            symbol = position.symbol
            volume = float(position.volume)
            is_buy = int(position.type) == int(getattr(mt5, "POSITION_TYPE_BUY", 0))
            close_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error("MT5 close: tick unavailable for %s", symbol)
                return False

            price = float(tick.bid if is_buy else tick.ask)
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "position": int(ticket),
                "price": price,
                "deviation": self.DEFAULT_DEVIATION,
                "magic": getattr(settings, "MAGIC_NUMBER", self.MAGIC_NUMBER),
                "comment": "Athena AI close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result is None:
                logger.error("MT5 close order_send returned None for ticket %s", ticket)
                return False

            retcode = getattr(result, "retcode", None)
            if retcode is not None and retcode not in _SUCCESS_RETCODES:
                logger.error(
                    "MT5 close rejected ticket=%s retcode=%s comment=%s",
                    ticket,
                    retcode,
                    getattr(result, "comment", ""),
                )
                return False

            logger.info("Closed MT5 ticket %s", ticket)
            return True

        # Pending order — cancel via TRADE_ACTION_REMOVE
        orders = mt5.orders_get(ticket=ticket)
        if not orders:
            logger.warning("MT5 close: position/order %s not found", ticket)
            return False

        request = {
            "action": getattr(mt5, "TRADE_ACTION_REMOVE", 8),
            "order": int(ticket),
            "comment": "Athena AI cancel",
        }
        result = mt5.order_send(request)
        if result is None:
            logger.error("MT5 cancel order_send returned None for ticket %s", ticket)
            return False

        retcode = getattr(result, "retcode", None)
        if retcode is not None and retcode not in _SUCCESS_RETCODES:
            logger.error(
                "MT5 cancel rejected ticket=%s retcode=%s comment=%s",
                ticket,
                retcode,
                getattr(result, "comment", ""),
            )
            return False

        logger.info("Cancelled MT5 pending order %s", ticket)
        return True

    def positions(
        self,
    ) -> list:
        rows: list[dict] = []

        open_positions = mt5.positions_get()
        if open_positions:
            for position in open_positions:
                rows.append(
                    {
                        "ticket": position.ticket,
                        "symbol": position.symbol,
                        "signal": "BUY" if position.type == 0 else "SELL",
                        "entry": position.price_open,
                        "stop_loss": position.sl,
                        "take_profit": position.tp,
                        "volume": position.volume,
                        "status": "OPEN",
                        "pnl": float(getattr(position, "profit", 0) or 0),
                    }
                )

        pending = mt5.orders_get()
        if pending:
            buy_limit = int(getattr(mt5, "ORDER_TYPE_BUY_LIMIT", 2))
            buy_stop = int(getattr(mt5, "ORDER_TYPE_BUY_STOP", 4))
            buy_stop_limit = int(getattr(mt5, "ORDER_TYPE_BUY_STOP_LIMIT", 6))
            buy_types = {buy_limit, buy_stop, buy_stop_limit, 0}

            for order in pending:
                order_type = int(getattr(order, "type", -1))
                signal = "BUY" if order_type in buy_types else "SELL"
                rows.append(
                    {
                        "ticket": order.ticket,
                        "symbol": order.symbol,
                        "signal": signal,
                        "entry": float(
                            getattr(order, "price_open", 0)
                            or getattr(order, "price_current", 0)
                            or 0
                        ),
                        "stop_loss": float(getattr(order, "sl", 0) or 0),
                        "take_profit": float(getattr(order, "tp", 0) or 0),
                        "volume": float(
                            getattr(order, "volume_current", 0)
                            or getattr(order, "volume_initial", 0)
                            or 0
                        ),
                        "status": "PENDING",
                        "pnl": 0.0,
                    }
                )

        return rows


mt5_execution = MT5ExecutionProvider()
