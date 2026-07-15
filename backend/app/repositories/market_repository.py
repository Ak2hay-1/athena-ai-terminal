"""
Market Repository.

Provides optimized database access for market candle data.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_
from sqlalchemy import delete
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_candle import MarketCandle
from app.repositories.base_repository import BaseRepository


class MarketRepository(BaseRepository[MarketCandle]):
    """
    Market candle repository.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:

        super().__init__(
            db=db,
            model=MarketCandle,
        )

    # ======================================================
    # Latest Candle
    # ======================================================

    def get_latest(
        self,
        symbol: str,
        timeframe: str,
    ) -> MarketCandle | None:
        """
        Return the latest candle.
        """

        stmt = (
            select(MarketCandle)
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
            )
            .order_by(
                desc(MarketCandle.time),
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    # ======================================================
    # Recent Candles
    # ======================================================

    def get_latest_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[MarketCandle]:
        """
        Return the latest N candles.
        """

        stmt = (
            select(MarketCandle)
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
            )
            .order_by(
                desc(MarketCandle.time),
            )
            .limit(limit)
        )

        candles = self.db.scalars(stmt).all()

        return list(reversed(candles))

    # ======================================================
    # History
    # ======================================================

    def get_history(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[MarketCandle]:
        """
        Return candles within a time range.
        """

        stmt = (
            select(MarketCandle)
            .where(
                and_(
                    MarketCandle.symbol == symbol,
                    MarketCandle.timeframe == timeframe,
                    MarketCandle.time >= start_time,
                    MarketCandle.time <= end_time,
                )
            )
            .order_by(
                MarketCandle.time,
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ======================================================
    # Exists
    # ======================================================

    def candle_exists(
        self,
        symbol: str,
        timeframe: str,
        candle_time: datetime,
    ) -> bool:
        """
        Check if a candle already exists.
        """

        stmt = (
            select(MarketCandle.id)
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
                MarketCandle.time == candle_time,
            )
            .limit(1)
        )

        return self.db.scalar(stmt) is not None

    # ======================================================
    # Existing Times
    # ======================================================

    def existing_times(
        self,
        symbol: str,
        timeframe: str,
        times: list[datetime],
    ) -> set[datetime]:
        """
        Return the subset of candle timestamps that already
        exist in the database.

        Used by CandleCollector to prevent duplicate inserts.
        """

        if not times:
            return set()

        stmt = (
            select(MarketCandle.time)
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
                MarketCandle.time.in_(times),
            )
        )

        return set(
            self.db.scalars(stmt).all()
        )

    # ======================================================
    # Statistics
    # ======================================================

    def get_statistics(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict:
        """
        Return candle statistics.
        """

        stmt = (
            select(
                func.count(MarketCandle.id),
                func.min(MarketCandle.time),
                func.max(MarketCandle.time),
            )
            .where(
                MarketCandle.symbol == symbol,
                MarketCandle.timeframe == timeframe,
            )
        )

        count, first, last = self.db.execute(stmt).one()

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_count": count,
            "first_candle": first,
            "last_candle": last,
        }

    # ======================================================
    # Bulk Insert
    # ======================================================

    def bulk_create(
        self,
        candles: list[MarketCandle],
    ) -> None:
        """
        Bulk insert candles.
        """

        self.db.add_all(candles)

    # ======================================================
    # Delete Old Data
    # ======================================================

    def delete_before(
        self,
        before: datetime,
    ) -> int:
        """
        Delete candles older than a timestamp.

        Returns the number of deleted rows.
        """

        stmt = (
            delete(MarketCandle)
            .where(
                MarketCandle.time < before,
            )
        )

        result = self.db.execute(stmt)

        return result.rowcount or 0
