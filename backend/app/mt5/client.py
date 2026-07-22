"""
MetaTrader 5 Client.

Provides a single interface for communicating with MetaTrader 5.
Returns ORM models instead of dictionaries.
"""

from __future__ import annotations

import multiprocessing
from datetime import UTC
from datetime import datetime

from app.mt5.sdk import mt5

from app.core.logger import logger
from app.core.settings import settings
from app.models.market_candle import MarketCandle
from app.mt5._init_probe import probe_initialize


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

        if not self._probe_reachable():

            logger.error(
                "MT5 unreachable: probe did not connect within %ss. "
                "Ensure the MT5 terminal is installed, running, and logged "
                "in on this machine.",
                settings.MT5_INIT_TIMEOUT,
            )

            return False

        # The probe already proved the terminal is reachable, so this
        # in-process call should return promptly.
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

    def _probe_reachable(self) -> bool:
        """
        Attempt mt5.initialize() in a throwaway subprocess with a hard
        timeout, so a hung/unreachable terminal can never freeze the app.

        A thread cannot substitute for this: the native MT5 call does not
        reliably release the GIL while blocked, so only killing the whole
        OS process guarantees recovery.
        """

        ctx = multiprocessing.get_context("spawn")
        result_queue: multiprocessing.Queue = ctx.Queue()

        process = ctx.Process(
            target=probe_initialize,
            args=(
                settings.MT5_PATH,
                settings.MT5_LOGIN,
                settings.MT5_PASSWORD,
                settings.MT5_SERVER,
                result_queue,
            ),
            daemon=True,
        )

        try:
            process.start()
            process.join(timeout=settings.MT5_INIT_TIMEOUT)

            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
                return False

            return bool(result_queue.get_nowait())

        except Exception as exc:

            logger.warning("MT5 reachability probe failed: %s", exc)

            return False

        finally:
            result_queue.close()

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

                    # Always UTC — naive fromtimestamp() uses the OS
                    # local zone (e.g. IST) and corrupts candle times.
                    time=datetime.fromtimestamp(
                        int(row["time"]),
                        tz=UTC,
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