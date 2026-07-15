"""
MetaTrader 5 Market Service.

Provides read-only market data operations.
"""

from __future__ import annotations

from datetime import datetime

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Manager
from app.mt5.mappers import MT5Mapper
from app.schemas.mt5 import (
    MT5Candle,
    MT5Quote,
    MT5SymbolInfo,
)

logger = get_logger(__name__)


class MarketService:
    """
    Market data service.

    Responsibilities
    ----------------
    - Symbols
    - Quotes
    - Candles

    This service intentionally does NOT perform
    trading operations.
    """

    def __init__(
        self,
        manager: IMT5Manager,
    ) -> None:
        self._manager = manager

    # =====================================================
    # Symbols
    # =====================================================

    def list_symbols(
        self,
    ) -> list[MT5SymbolInfo]:
        """
        Return all available symbols.
        """

        logger.debug("Loading MT5 symbols.")

        symbols = self._manager.symbols()

        return [
            MT5Mapper.symbol(symbol)
            for symbol in symbols
        ]

    def get_symbol(
        self,
        symbol: str,
    ) -> MT5SymbolInfo:
        """
        Return symbol information.
        """

        logger.debug(
            "Loading symbol information: %s",
            symbol,
        )

        info = self._manager.symbol_info(symbol)

        return MT5Mapper.symbol(info)

    def select_symbol(
        self,
        symbol: str,
        enable: bool = True,
    ) -> bool:
        """
        Enable or disable a symbol.
        """

        logger.debug(
            "Selecting symbol %s (%s)",
            symbol,
            enable,
        )

        return self._manager.symbol_select(
            symbol=symbol,
            enable=enable,
        )

    # =====================================================
    # Quotes
    # =====================================================

    def get_tick(
        self,
        symbol: str,
    ) -> MT5Quote:
        """
        Return latest market quote.
        """

        logger.debug(
            "Loading latest tick for %s",
            symbol,
        )

        tick = self._manager.symbol_tick(symbol)

        return MT5Mapper.quote(
            tick=tick,
            symbol=symbol,
        )

    # =====================================================
    # Candles
    # =====================================================

    def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        count: int,
        start: int = 0,
    ) -> list[MT5Candle]:
        """
        Return recent candles.
        """

        logger.debug(
            "Loading %s candles (%s)",
            symbol,
            timeframe,
        )

        candles = self._manager.copy_rates_from_pos(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            count=count,
        )

        return [
            MT5Mapper.candle(candle)
            for candle in candles
        ]

    def get_candles_range(
        self,
        *,
        symbol: str,
        timeframe: str,
        from_time: datetime,
        to_time: datetime,
    ) -> list[MT5Candle]:
        """
        Return candles within a time range.
        """

        logger.debug(
            "Loading candle range %s (%s)",
            symbol,
            timeframe,
        )

        candles = self._manager.copy_rates_range(
            symbol=symbol,
            timeframe=timeframe,
            from_time=from_time,
            to_time=to_time,
        )

        return [
            MT5Mapper.candle(candle)
            for candle in candles
        ]
