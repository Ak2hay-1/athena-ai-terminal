"""
Market Service.

Business logic for market data operations.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.recommendation_engine import recommendation_engine
from app.core.exceptions import ValidationException
from app.models.market_candle import MarketCandle
from app.repositories.market_repository import MarketRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.market import (
    MarketCandleCreate,
    MarketCandleRead,
    MarketStatistics,
)
from app.services.base_service import BaseService


class MarketService(BaseService):
    """
    Market data business logic.
    """

    MIN_ANALYSIS_CANDLES = 50

    def __init__(
        self,
        db: Session,
    ) -> None:

        super().__init__(db)

        self.market = MarketRepository(db)

    # ======================================================
    # Create Candle
    # ======================================================

    def create_candle(
        self,
        payload: MarketCandleCreate,
    ) -> MarketCandleRead:
        """
        Insert a new market candle.
        """

        if self.market.candle_exists(
            payload.symbol,
            payload.timeframe,
            payload.time,
        ):
            raise ValidationException(
                "Market candle already exists."
            )

        candle = MarketCandle(
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            time=payload.time,
            open=payload.open,
            high=payload.high,
            low=payload.low,
            close=payload.close,
            tick_volume=payload.tick_volume,
            spread=payload.spread,
            real_volume=payload.real_volume,
        )

        self.market.create(candle)

        self.commit()

        self.refresh(candle)

        self.logger.info(
            "Created candle %s %s %s",
            candle.symbol,
            candle.timeframe,
            candle.time,
        )

        return MarketCandleRead.model_validate(
            candle,
        )

    # ======================================================
    # Bulk Insert
    # ======================================================

    def bulk_insert(
        self,
        payload: list[MarketCandleCreate],
    ) -> int:
        """
        Insert multiple candles.

        Duplicate candles are skipped.
        """

        candles: list[MarketCandle] = []

        for item in payload:

            if self.market.candle_exists(
                item.symbol,
                item.timeframe,
                item.time,
            ):
                continue

            candles.append(
                MarketCandle(
                    symbol=item.symbol,
                    timeframe=item.timeframe,
                    time=item.time,
                    open=item.open,
                    high=item.high,
                    low=item.low,
                    close=item.close,
                    tick_volume=item.tick_volume,
                    spread=item.spread,
                    real_volume=item.real_volume,
                )
            )

        if not candles:
            return 0

        self.market.bulk_create(candles)

        self.commit()

        self.logger.info(
            "Inserted %d candles.",
            len(candles),
        )

        return len(candles)

    # ======================================================
    # Latest Candle
    # ======================================================

    def get_latest(
        self,
        symbol: str,
        timeframe: str,
    ) -> MarketCandleRead:

        candle = self.market.get_latest(
            symbol,
            timeframe,
        )

        if candle is None:
            raise ValidationException(
                "No market data found."
            )

        return MarketCandleRead.model_validate(
            candle,
        )

    # ======================================================
    # Latest Candles
    # ======================================================

    def get_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[MarketCandleRead]:

        candles = self.market.get_latest_candles(
            symbol,
            timeframe,
            limit,
        )

        return [
            MarketCandleRead.model_validate(
                candle,
            )
            for candle in candles
        ]

    # ======================================================
    # History
    # ======================================================

    def get_history(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MarketCandleRead]:

        if start_time >= end_time:
            raise ValidationException(
                "Invalid date range."
            )

        candles = self.market.get_history(
            symbol,
            timeframe,
            start_time,
            end_time,
        )

        return [
            MarketCandleRead.model_validate(
                candle,
            )
            for candle in candles
        ]

    # ======================================================
    # Statistics
    # ======================================================

    def get_statistics(
        self,
        symbol: str,
        timeframe: str,
    ) -> MarketStatistics:

        stats = self.market.get_statistics(
            symbol,
            timeframe,
        )

        return MarketStatistics.model_validate(
            stats,
        )

    # ======================================================
    # Analyze Latest Market Data
    # ======================================================

    def analyze_latest(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ):
        """
        Analyze the latest market candles and persist
        an AI recommendation.
        """

        candles = self.market.get_latest_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if len(candles) < self.MIN_ANALYSIS_CANDLES:
            self.logger.warning(
                "Not enough candles for analysis."
            )
            return None

        dataframe = self._candles_to_dataframe(
            candles
        )

        repository = RecommendationRepository(
            self.db
        )

        try:

            recommendation = recommendation_engine.analyze(
                dataframe=dataframe,
                repository=repository,
            )

            self.commit()

        except Exception:

            self.rollback()

            self.logger.exception(
                "Recommendation analysis failed for %s %s",
                symbol,
                timeframe,
            )

            return None

        self.logger.info(
            "%s %s -> %s (%d%%)",
            symbol,
            timeframe,
            recommendation.signal,
            recommendation.confidence,
        )

        return recommendation

    # ======================================================
    # Analyze Multiple Symbols
    # ======================================================

    def analyze_all(
        self,
        symbols: list[str],
        timeframe: str,
    ) -> None:
        """
        Analyze multiple symbols.
        """

        for symbol in symbols:

            self.analyze_latest(
                symbol=symbol,
                timeframe=timeframe,
            )

    # ======================================================
    # Helpers
    # ======================================================

    def _candles_to_dataframe(
        self,
        candles: list[MarketCandleRead],
    ) -> pd.DataFrame:
        """
        Convert market candles to a pandas DataFrame.
        """

        return pd.DataFrame(
            [
                {
                    "time": candle.time,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "tick_volume": candle.tick_volume,
                }
                for candle in candles
            ]
        )

    # ======================================================
    # Cleanup
    # ======================================================

    def delete_before(
        self,
        before: datetime,
    ) -> int:
        """
        Delete candles older than the specified timestamp.
        """

        deleted = self.market.delete_before(
            before,
        )

        self.commit()

        self.logger.info(
            "Deleted %d historical candles.",
            deleted,
        )

        return deleted
