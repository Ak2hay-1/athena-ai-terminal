"""
Market Service.

Business logic for market data operations.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.recommendation_engine import recommendation_engine
from app.ai.schemas.context import MarketContext
from app.core.exceptions import ValidationException
from app.models.market_candle import MarketCandle
from app.repositories.market_repository import MarketRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.market import (
    MarketBackfillResult,
    MarketCandleCreate,
    MarketCandleRead,
    MarketQuote,
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

        from app.core.settings import settings

        if settings.CACHE_ENABLED:
            from app.cache import cache_manager

            payload = cache_manager.get_latest_candle(symbol, timeframe)
            if payload is not None:
                return MarketCandleRead.model_validate(payload)

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
        before: datetime | None = None,
    ) -> list[MarketCandleRead]:
        """
        Serve candles through CacheManager (RAM → DB → MT5 gap sync).

        Forming live bars are never returned as immutable history.
        """

        from app.core.settings import settings

        if settings.CACHE_ENABLED:
            from app.cache import cache_manager

            payloads = cache_manager.get_candles(
                symbol,
                timeframe,
                limit=limit,
                before=before,
                sync_if_stale=before is None,
                trigger_preload=before is None,
            )
            return [
                MarketCandleRead.model_validate(payload)
                for payload in payloads
            ]

        candles = self.market.get_latest_candles(
            symbol,
            timeframe,
            limit,
            before=before,
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
    # Live Quotes
    # ======================================================

    def get_quotes(
        self,
        symbols: list[str],
        timeframe: str = "M1",
    ) -> list[MarketQuote]:
        """
        Return live mid quotes from the live market cache (Redis /
        in-memory, fed by the tick engine), falling back to direct MT5
        only when the engine is disabled, then to the latest candle
        close.
        """

        quotes: list[MarketQuote] = []

        for raw_symbol in symbols:
            symbol = raw_symbol.upper().strip()
            if not symbol:
                continue

            tick = self._live_tick(symbol)

            if tick is not None:
                bid = float(tick.get("bid") or 0)
                ask = float(tick.get("ask") or 0)
                mid = float(tick.get("mid") or 0)
                if not mid:
                    mid = (bid + ask) / 2 if bid and ask else bid or ask
                if mid:
                    quotes.append(
                        MarketQuote(
                            symbol=symbol,
                            bid=bid,
                            ask=ask,
                            mid=mid,
                            time=self._parse_tick_time(tick.get("time")),
                            source="tick",
                        )
                    )
                    continue

            candle = self.market.get_latest(
                symbol,
                timeframe.upper(),
            )
            if candle is None:
                continue

            close = float(candle.close)
            quotes.append(
                MarketQuote(
                    symbol=symbol,
                    bid=close,
                    ask=close,
                    mid=close,
                    time=candle.time,
                    source="candle",
                )
            )

        return quotes

    def _live_tick(self, symbol: str) -> dict | None:
        """Latest tick from the live cache, or MT5 as legacy fallback."""

        from app.core.settings import settings
        from app.marketdata.live_cache import live_market_cache

        cached = live_market_cache.get_tick(symbol)
        if cached is not None:
            return cached

        if settings.MARKET_ENGINE_ENABLED:
            return None

        try:
            from app.market.adapter import market as mt5_market

            tick = mt5_market.tick(symbol)
        except Exception:
            self.logger.exception("Tick fetch failed for %s", symbol)
            return None

        if tick is None:
            return None

        raw_time = tick.get("time")
        return {
            "bid": tick.get("bid"),
            "ask": tick.get("ask"),
            "mid": None,
            "time": datetime.fromtimestamp(
                int(raw_time),
                tz=timezone.utc,
            ).isoformat()
            if raw_time
            else None,
        }

    @staticmethod
    def _parse_tick_time(value) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

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
    # Deep MT5 Backfill
    # ======================================================

    def backfill_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int | None = None,
    ) -> MarketBackfillResult:
        """
        Pull as many bars as allowed from MT5 into Postgres.
        """
        from app.core.exceptions import MT5Exception
        from app.core.settings import settings
        from app.mt5.candle_collector import CandleCollector
        from app.mt5.client import mt5_client

        symbol = symbol.upper()
        timeframe = timeframe.upper()

        if not mt5_client.initialize():
            raise MT5Exception(
                "MetaTrader 5 is not connected. Set MT5_LOGIN, MT5_PASSWORD, "
                "MT5_SERVER (and MT5_PATH if needed) in backend/.env, open the "
                "MT5 terminal on Windows, then restart the API."
            )

        max_bars = max(1, int(settings.MARKET_BACKFILL_BARS))
        requested = max_bars if count is None else max(1, min(int(count), max_bars))

        collector = CandleCollector(self.db)
        # Chunk large requests so a single MT5 call stays within broker limits.
        chunk = min(requested, max(1, int(settings.MARKET_COLLECTOR_BARS)))
        remaining = requested
        inserted_total = 0

        while remaining > 0:
            pull = min(chunk, remaining)
            inserted_total += collector.collect(
                symbol,
                timeframe,
                count=pull,
            )
            # After first deep pull, further chunks from pos=0 return the same
            # newest bars; stop once one pass completes.
            remaining = 0

        stats = self.market.get_statistics(symbol, timeframe)
        candle_count = int(stats.get("candle_count") or 0)

        if inserted_total == 0 and candle_count == 0:
            raise MT5Exception(
                f"No candle data returned from MT5 for {symbol} {timeframe}. "
                "Confirm the symbol matches your broker Market Watch name "
                "(e.g. GBPUSD vs GBPUSDm) and that history is available."
            )

        return MarketBackfillResult(
            symbol=symbol,
            timeframe=timeframe,
            requested=requested,
            inserted=inserted_total,
            candle_count=candle_count,
            oldest=stats.get("first_candle"),
            newest=stats.get("last_candle"),
        )

    def maybe_startup_backfill(
        self,
        symbol: str,
        timeframe: str,
    ) -> MarketBackfillResult | None:
        """
        If DB depth is below threshold, run a one-shot deep backfill.
        """
        from app.core.settings import settings

        if not settings.MARKET_STARTUP_BACKFILL_ENABLED:
            return None

        stats = self.market.get_statistics(symbol, timeframe)
        count = int(stats.get("candle_count") or 0)
        threshold = max(0, int(settings.MARKET_STARTUP_BACKFILL_THRESHOLD))
        if count >= threshold:
            return None

        self.logger.info(
            "Startup backfill %s %s (have=%d threshold=%d)",
            symbol,
            timeframe,
            count,
            threshold,
        )
        return self.backfill_candles(
            symbol,
            timeframe,
            count=settings.MARKET_BACKFILL_BARS,
        )

    # ======================================================
    # Analyze Latest Market Data
    # ======================================================

    def analyze_latest(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        *,
        explain_with_ai: bool = True,
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

        news_context = None
        weights = None
        higher_timeframes = None

        try:
            from app.learning.adaptive_weights import AdaptiveWeightEngine
            from app.services.news_service import NewsService

            news_context = NewsService(self.db).get_context_for_symbol(
                symbol
            )
            weights = AdaptiveWeightEngine(self.db).get_weights(
                symbol,
                timeframe,
            )
            higher_timeframes = self._load_higher_timeframes(
                symbol,
                timeframe,
            )

        except Exception:

            self.logger.exception(
                "Optional context load failed for %s %s",
                symbol,
                timeframe,
            )

        try:

            recommendation = recommendation_engine.analyze(
                dataframe=dataframe,
                symbol=symbol,
                timeframe=timeframe,
                repository=repository,
                news_context=news_context,
                higher_timeframes=higher_timeframes,
                weights=weights,
                explain_with_ai=explain_with_ai,
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

        try:
            from app.services.websocket_broadcast import broadcast_scanner_update

            signal = recommendation.signal
            if hasattr(signal, "value"):
                signal = signal.value
            broadcast_scanner_update(
                symbol=symbol,
                timeframe=timeframe,
                change_type="recommendation",
                opportunity={
                    "symbol": symbol.upper(),
                    "timeframe": timeframe.upper(),
                    "signal": str(signal),
                    "confidence": int(recommendation.confidence or 0),
                    "entry": float(recommendation.entry)
                    if getattr(recommendation, "entry", None) is not None
                    else None,
                    "stop_loss": float(recommendation.stop_loss)
                    if getattr(recommendation, "stop_loss", None) is not None
                    else None,
                    "take_profit": float(recommendation.take_profit)
                    if getattr(recommendation, "take_profit", None) is not None
                    else None,
                    "risk_reward": float(getattr(recommendation, "risk_reward", 0) or 0),
                    "trend": str(getattr(recommendation, "trend", "") or ""),
                },
            )
        except Exception:
            self.logger.exception(
                "scanner_update broadcast failed for %s %s",
                symbol,
                timeframe,
            )

        try:
            from app.trading.auto_trade import AutoTradeService

            AutoTradeService(self.db).process(recommendation)
        except Exception:
            self.logger.exception(
                "Auto-trade processing failed for %s %s",
                symbol,
                timeframe,
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
    # Slim AI Market Context (no candles to LLM)
    # ======================================================

    def build_ai_market_context(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> MarketContext | None:
        """
        Build structured MarketContext for AIService.

        Runs local analyzers only; never returns OHLC series.
        """

        from app.analysis.market_analyzer import market_analyzer
        from app.analysis.multi_timeframe_analyzer import multi_timeframe_analyzer

        candles = self.market.get_latest_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        if len(candles) < self.MIN_ANALYSIS_CANDLES:
            return None

        dataframe = self._candles_to_dataframe(candles)
        news_context = None
        weights = None
        multi_tf = None

        try:
            from app.learning.adaptive_weights import AdaptiveWeightEngine
            from app.services.news_service import NewsService

            news_context = NewsService(self.db).get_context_for_symbol(symbol)
            weights = AdaptiveWeightEngine(self.db).get_weights(symbol, timeframe)
            higher = self._load_higher_timeframes(symbol, timeframe)
            if higher:
                multi_tf = multi_timeframe_analyzer.analyze(higher)
        except Exception:
            self.logger.exception(
                "Optional AI context load failed for %s %s",
                symbol,
                timeframe,
            )

        analysis = market_analyzer.analyze(
            dataframe,
            news_context=news_context,
            multi_timeframe=multi_tf,
            weights=weights,
        )
        return MarketContext.from_analysis(
            analysis,
            symbol=symbol,
            timeframe=timeframe,
        )

    # ======================================================
    # Helpers
    # ======================================================

    def _load_higher_timeframes(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, pd.DataFrame]:
        from app.core.settings import settings

        context_tfs = settings.MULTI_TF_CONTEXT.get(
            timeframe,
            [],
        )

        frames: dict[str, pd.DataFrame] = {}

        for tf in context_tfs:

            candles = self.market.get_latest_candles(
                symbol=symbol,
                timeframe=tf,
                limit=500,
            )

            if len(candles) < self.MIN_ANALYSIS_CANDLES:
                continue

            frames[tf] = self._candles_to_dataframe(candles)

        return frames

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
