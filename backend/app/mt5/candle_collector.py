"""
High-performance MT5 Candle Collector.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import MetaTrader5 as mt5
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.market_candle import MarketCandle
from app.mt5.client import mt5_client
from app.repositories.market_repository import (
    MarketRepository,
)


class CandleCollector:

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db
        self.repository = MarketRepository(db)

    # ==========================================================
    # Internal Collector
    # ==========================================================

    def _collect(
        self,
        symbol: str,
        timeframe: int,
        timeframe_name: str,
        count: int = 500,
    ) -> int:

        rates = mt5_client.copy_rates(
            symbol=symbol,
            timeframe=timeframe,
            timeframe_name=timeframe_name,
            count=count,
        )

        if not rates:

            logger.warning(
                "%s %s -> No candles",
                symbol,
                timeframe_name,
            )

            return 0

        candles: list[MarketCandle] = []

        for rate in rates:

            # MT5 may return either a Unix timestamp
            # or a datetime object.
            if isinstance(rate.time, datetime):

                candle_time = rate.time

                if candle_time.tzinfo is None:

                    candle_time = candle_time.replace(
                        tzinfo=UTC,
                    )

            else:

                candle_time = datetime.fromtimestamp(
                    float(rate.time),
                    tz=UTC,
                )

            candles.append(
                MarketCandle(
                    symbol=symbol,
                    timeframe=timeframe_name,
                    time=candle_time,
                    open=float(rate.open),
                    high=float(rate.high),
                    low=float(rate.low),
                    close=float(rate.close),
                    tick_volume=int(rate.tick_volume),
                    spread=int(rate.spread),
                    real_volume=int(rate.real_volume),
                )
            )

        times = [
            candle.time
            for candle in candles
        ]

        existing = self.repository.existing_times(
            symbol=symbol,
            timeframe=timeframe_name,
            times=times,
        )

        new_candles = [
            candle
            for candle in candles
            if candle.time not in existing
        ]

        if not new_candles:

            logger.info(
                "%s %s -> No new candles",
                symbol,
                timeframe_name,
            )

            return 0

        self.repository.bulk_create(
            new_candles,
        )

        self.db.commit()

        inserted = len(new_candles)

        logger.info(
            "%s %s -> %d new candles",
            symbol,
            timeframe_name,
            inserted,
        )

        return inserted

    # ==========================================================
    # Generic Collector
    # ==========================================================

    def collect(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        """
        Collect candles for any supported timeframe.
        """

        mapping = {
            "M1": self.collect_m1,
            "M5": self.collect_m5,
            "M15": self.collect_m15,
            "M30": self.collect_m30,
            "H1": self.collect_h1,
            "H4": self.collect_h4,
            "D1": self.collect_d1,
        }

        collector = mapping.get(timeframe)

        if collector is None:

            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        return collector(symbol)

    # ==========================================================
    # Timeframe Helpers
    # ==========================================================

    def collect_m1(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_M1,
            "M1",
        )

    def collect_m5(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_M5,
            "M5",
        )

    def collect_m15(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_M15,
            "M15",
        )

    def collect_m30(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_M30,
            "M30",
        )

    def collect_h1(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_H1,
            "H1",
        )

    def collect_h4(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_H4,
            "H4",
        )

    def collect_d1(
        self,
        symbol: str,
    ) -> int:

        return self._collect(
            symbol,
            mt5.TIMEFRAME_D1,
            "D1",
        )
