"""
MetaTrader 5 Client.

Provides a single interface for communicating with MetaTrader 5.
Returns ORM models instead of dictionaries.
"""

from __future__ import annotations

from datetime import datetime

import MetaTrader5 as mt5

from app.core.logger import logger
from app.core.settings import settings
from app.models.market_candle import MarketCandle


class MT5Client:
    """
    MetaTrader 5 Client.
    """

    def __init__(self) -> None:

        self.connected = False

    # =====================================================
    # Connection
    # =====================================================

    def initialize(self) -> bool:

        if self.connected:
            return True

        initialized = mt5.initialize(
            path=settings.MT5_PATH,
            login=settings.MT5_LOGIN,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER,
        )

        if not initialized:

            logger.error(
                "MT5 initialization failed: %s",
                mt5.last_error(),
            )

            return False

        self.connected = True

        logger.info("Connected to MetaTrader 5.")

        return True

    def shutdown(self) -> None:

        if self.connected:

            mt5.shutdown()

            self.connected = False

            logger.info("Disconnected from MT5.")

    # =====================================================
    # Market Data
    # =====================================================

    def copy_rates(
        self,
        symbol: str,
        timeframe: int,
        timeframe_name: str,
        count: int = 500,
    ) -> list[MarketCandle]:

        if not self.initialize():

            return []

        rates = mt5.copy_rates_from_pos(
            symbol,
            timeframe,
            0,
            count,
        )

        if rates is None:

            logger.warning(
                "No rates returned for %s",
                symbol,
            )

            return []

        candles: list[MarketCandle] = []

        for row in rates:

            candles.append(

                MarketCandle(

                    symbol=symbol,

                    timeframe=timeframe_name,

                    time=datetime.fromtimestamp(
                        int(row["time"])
                    ),

                    open=float(row["open"]),

                    high=float(row["high"]),

                    low=float(row["low"]),

                    close=float(row["close"]),

                    tick_volume=int(
                        row["tick_volume"]
                    ),

                    spread=int(
                        row["spread"]
                    ),

                    real_volume=int(
                        row["real_volume"]
                    ),

                )

            )

        return candles

    # =====================================================
    # Helpers
    # =====================================================

    def account_info(self):

        return mt5.account_info()

    def terminal_info(self):

        return mt5.terminal_info()

    def symbols(self) -> list[str]:

        symbols = mt5.symbols_get()

        if symbols is None:

            return []

        return sorted(
            symbol.name
            for symbol in symbols
        )


mt5_client = MT5Client()