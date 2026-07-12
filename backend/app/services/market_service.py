"""
Market Service.

Responsible for synchronizing MT5 market data with PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.market.adapter import market
from app.models.market_candle import MarketCandle
from app.repositories.market_candle_repository import MarketCandleRepository


class MarketService:
    """
    Handles market data operations.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = MarketCandleRepository(db)

    def sync_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500,
    ) -> int:
        """
        Download candles from MT5 and store only new candles.
        """

        candles = market.candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )

        inserted = 0

        for candle in candles:

            if self.repository.exists(
                symbol=symbol,
                timeframe=timeframe,
                candle_time=candle["time"],
            ):
                continue

            model = MarketCandle(
                symbol=symbol,
                timeframe=timeframe,
                time=candle["time"],
                open=candle["open"],
                high=candle["high"],
                low=candle["low"],
                close=candle["close"],
                tick_volume=candle["tick_volume"],
                spread=candle["spread"],
                real_volume=candle["real_volume"],
            )

            self.repository.create(model)

            inserted += 1

        logger.info(
            "%s %s -> %s candles inserted",
            symbol,
            timeframe,
            inserted,
        )

        return inserted

    def latest(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ):
        """
        Return latest candles from the database.
        """

        return self.repository.get_latest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    def symbols(self):
        """
        Return available MT5 symbols.
        """

        return market.symbols()

    def tick(self, symbol: str):
        """
        Return latest MT5 tick.
        """

        return market.tick(symbol)