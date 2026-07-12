"""
Repository for Market Candle operations.
"""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_candle import MarketCandle


class MarketCandleRepository:
    """
    Repository responsible for all Market Candle database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, candle: MarketCandle) -> MarketCandle:
        """
        Insert a candle into the database.
        """
        self.db.add(candle)
        self.db.commit()
        self.db.refresh(candle)
        return candle

    def bulk_create(self, candles: List[MarketCandle]) -> None:
        """
        Insert multiple candles.
        """
        self.db.add_all(candles)
        self.db.commit()

    def get_latest(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> List[MarketCandle]:
        """
        Get latest candles.
        """
        stmt = (
            select(MarketCandle)
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
            )
            .order_by(MarketCandle.time.desc())
            .limit(limit)
        )

        return list(self.db.scalars(stmt).all())

    def exists(
        self,
        symbol: str,
        timeframe: str,
        candle_time,
    ) -> bool:
        """
        Check whether a candle already exists.
        """
        stmt = select(MarketCandle).where(
            MarketCandle.symbol == symbol,
            MarketCandle.timeframe == timeframe,
            MarketCandle.time == candle_time,
        )

        return self.db.scalar(stmt) is not None

    def delete_all(self) -> None:
        """
        Delete all candles.
        """
        self.db.query(MarketCandle).delete()
        self.db.commit()