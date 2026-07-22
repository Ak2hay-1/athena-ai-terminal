"""
Incremental Indicator Updater.

Recomputes indicator values only when a candle closes, and only for the
newly completed candle (using a bounded warm-up window of recent local
candles — never the entire history). Values are persisted to the
indicator_values table and mirrored to the Redis live cache.
"""

from __future__ import annotations

import math

from app.core.logger import get_logger
from app.core.settings import settings
from app.marketdata.engine import Candle
from app.marketdata.live_cache import live_market_cache
from app.marketdata.timeframes import epoch_to_datetime

logger = get_logger("athena.marketdata.indicators")

# Warm-up bars so EMA/RSI/ATR values converge before the newest bar.
_WINDOW = 200


class IndicatorUpdater:
    """Per-candle-close indicator computation and persistence."""

    def on_candle_closed(self, candle: Candle) -> dict | None:
        """
        Compute and persist indicator values for one completed candle.

        Returns the computed values (also written to Redis) or None.
        """

        try:
            values = self._compute(candle)
        except Exception:
            logger.exception(
                "Indicator update failed for %s %s",
                candle.symbol,
                candle.timeframe,
            )
            return None

        if not values:
            return None

        try:
            self._persist(candle, values)
        except Exception:
            logger.exception(
                "Indicator persistence failed for %s %s",
                candle.symbol,
                candle.timeframe,
            )

        live_market_cache.set_indicators(
            candle.symbol,
            candle.timeframe,
            {
                "symbol": candle.symbol,
                "timeframe": candle.timeframe,
                "time": epoch_to_datetime(candle.bucket_start).isoformat(),
                "values": values,
            },
        )

        try:
            from app.cache import cache_manager
            from app.core.settings import settings as _settings

            if _settings.CACHE_ENABLED:
                # Fingerprint against the closed bar so unchanged series
                # reuses this payload on the next indicator read.
                cache_manager.ram.put_indicators(
                    f"{candle.symbol.upper()}:{candle.timeframe.upper()}:ind",
                    fingerprint=str(candle.bucket_start),
                    values=values,
                )
        except Exception:
            pass

        return values

    # ------------------------------------------------------------------

    def _compute(self, candle: Candle) -> dict:
        import pandas as pd

        from app.database.database import SessionLocal
        from app.indicators.indicator_engine import indicator_engine
        from app.repositories.market_repository import MarketRepository

        db = SessionLocal()
        try:
            repository = MarketRepository(db)
            candles = repository.get_latest_candles(
                candle.symbol,
                candle.timeframe,
                limit=_WINDOW,
            )
        finally:
            db.close()

        rows = [
            {
                "time": row.time,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "tick_volume": row.tick_volume,
            }
            for row in candles
        ]

        # The freshly closed candle may still be queued in the batched
        # writer; append it so indicators reflect the newest bar.
        candle_time = epoch_to_datetime(candle.bucket_start)
        if not rows or rows[-1]["time"] < candle_time:
            rows.append(
                {
                    "time": candle_time,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "tick_volume": candle.tick_volume,
                }
            )

        if len(rows) < 30:
            return {}

        frame = pd.DataFrame(rows)

        result = indicator_engine.calculate(frame)
        last = result.iloc[-1]

        base_columns = {"time", "open", "high", "low", "close", "tick_volume"}
        values: dict = {}
        for column in result.columns:
            if column in base_columns:
                continue
            value = last[column]
            if value is None:
                continue
            if isinstance(value, float) and math.isnan(value):
                continue
            try:
                values[column] = float(value)
            except (TypeError, ValueError):
                continue

        return values

    def _persist(self, candle: Candle, values: dict) -> None:
        from sqlalchemy.dialects.postgresql import insert

        from app.database.database import SessionLocal
        from app.models.indicator_value import IndicatorValue

        db = SessionLocal()
        try:
            stmt = (
                insert(IndicatorValue)
                .values(
                    symbol=candle.symbol,
                    timeframe=candle.timeframe,
                    time=epoch_to_datetime(candle.bucket_start),
                    values=values,
                    indicator_version=settings.INDICATOR_VERSION,
                )
                .on_conflict_do_update(
                    constraint="uq_indicator_value",
                    set_={
                        "values": values,
                        "indicator_version": settings.INDICATOR_VERSION,
                    },
                )
            )
            db.execute(stmt)
            db.commit()
        finally:
            db.close()


indicator_updater = IndicatorUpdater()
