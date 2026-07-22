"""
Recommendation outcome tracker.

Detects TP hit, SL hit, manual paper exit, or timeout from subsequent candles.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models.learning import OutcomeResult
from app.models.learning import RecommendationOutcome
from app.models.paper_position import PaperPosition
from app.models.recommendation import Recommendation
from app.repositories.learning_repository import LearningRepository
from app.repositories.market_repository import MarketRepository


class OutcomeTracker:
    """Label completed recommendations with explainable exit results."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.learning = LearningRepository(db)
        self.market = MarketRepository(db)

    def label_pending(self, limit: int = 200) -> int:
        pending = self.learning.get_unlabeled_recommendations(limit=limit)
        labeled = 0
        horizon = settings.LEARNING_OUTCOME_HORIZON_CANDLES

        for recommendation in pending:
            if self.learning.outcome_exists(recommendation.id):
                continue
            signal_name = str(
                getattr(recommendation.signal, "value", recommendation.signal)
            ).upper()
            if signal_name in {"HOLD", "NO_TRADE"}:
                continue

            try:
                outcome = self._label_one(recommendation, horizon)
            except Exception:
                logger.exception(
                    "Outcome labeling failed for recommendation %s",
                    recommendation.id,
                )
                continue

            if outcome is None:
                continue
            self.learning.save_outcome(outcome)
            labeled += 1

        if labeled:
            self.db.commit()
        return labeled

    def _label_one(
        self,
        recommendation: Recommendation,
        horizon: int,
    ) -> RecommendationOutcome | None:
        manual = self._manual_exit(recommendation)
        if manual is not None:
            return manual

        candles = self.market.get_latest_candles(
            recommendation.symbol,
            recommendation.timeframe,
            limit=horizon + 20,
        )
        if len(candles) < horizon + 1:
            return None

        # Prefer candles after recommendation time when timestamps exist.
        after = self._candles_after(candles, recommendation)
        if len(after) < 1:
            after = candles[-(horizon):]
        else:
            after = after[:horizon]

        if not after:
            return None

        entry = self._entry_price(recommendation, after[0])
        sl = float(recommendation.stop_loss or 0.0)
        tp = float(recommendation.take_profit or 0.0)
        rr = float(recommendation.risk_reward or 0.0)
        signal = str(
            getattr(recommendation.signal, "value", recommendation.signal)
        ).upper()
        confidence = int(recommendation.confidence or 0)
        regime = getattr(recommendation, "market_regime", None)

        result, exit_price, bars_held = self._detect_path(
            signal=signal,
            entry=entry,
            sl=sl,
            tp=tp,
            candles=after,
        )

        label = self._label_from_result(result, entry, exit_price, signal)
        profit = self._signed_pnl(signal, entry, exit_price)
        duration = self._duration_minutes(recommendation, after, bars_held)

        return RecommendationOutcome(
            recommendation_id=recommendation.id,
            symbol=recommendation.symbol,
            timeframe=recommendation.timeframe,
            predicted_signal=signal,
            label=label,
            pnl_proxy=profit,
            horizon_candles=horizon,
            labeled_at=datetime.now(timezone.utc),
            result=result,
            entry=entry,
            sl=sl or None,
            tp=tp or None,
            rr=rr or None,
            profit=profit,
            duration_minutes=duration,
            regime=regime,
            confidence_at_entry=confidence,
        )

    def _manual_exit(
        self,
        recommendation: Recommendation,
    ) -> RecommendationOutcome | None:
        row = (
            self.db.query(PaperPosition)
            .filter(
                PaperPosition.recommendation_id == recommendation.id,
                PaperPosition.status == "CLOSED",
            )
            .order_by(PaperPosition.closed_at.desc())
            .first()
        )
        if row is None:
            return None

        entry = float(row.entry)
        exit_price = entry + float(row.pnl or 0.0)  # pnl stored as price delta proxy
        # Prefer reconstructing exit from pnl if signal known
        signal = str(row.signal or recommendation.signal).upper()
        if signal == "BUY":
            exit_price = entry + float(row.pnl or 0.0)
        elif signal == "SELL":
            exit_price = entry - float(row.pnl or 0.0)
        else:
            exit_price = entry

        profit = float(row.pnl or 0.0)
        if profit > 0:
            label = "WIN"
        elif profit < 0:
            label = "LOSS"
        else:
            label = "NEUTRAL"

        duration = None
        if row.opened_at and row.closed_at:
            duration = int((row.closed_at - row.opened_at).total_seconds() // 60)

        return RecommendationOutcome(
            recommendation_id=recommendation.id,
            symbol=recommendation.symbol,
            timeframe=recommendation.timeframe,
            predicted_signal=signal,
            label=label,
            pnl_proxy=profit,
            horizon_candles=settings.LEARNING_OUTCOME_HORIZON_CANDLES,
            labeled_at=datetime.now(timezone.utc),
            result=OutcomeResult.MANUAL_EXIT.value,
            entry=entry,
            sl=float(row.stop_loss),
            tp=float(row.take_profit),
            rr=float(recommendation.risk_reward or 0.0) or None,
            profit=profit,
            duration_minutes=duration,
            regime=getattr(recommendation, "market_regime", None),
            confidence_at_entry=int(recommendation.confidence or 0),
        )

    @staticmethod
    def _entry_price(recommendation: Recommendation, fallback_candle: Any) -> float:
        entry = getattr(recommendation, "entry_price", None)
        if entry is not None:
            return float(entry)
        legacy = getattr(recommendation, "entry", None)
        if legacy is not None:
            return float(legacy)
        return float(getattr(fallback_candle, "close", 0.0) or 0.0)

    @staticmethod
    def _candles_after(candles: list, recommendation: Recommendation) -> list:
        created = getattr(recommendation, "created_at", None)
        if created is None:
            return []
        after = []
        for candle in candles:
            ts = getattr(candle, "time", None) or getattr(candle, "timestamp", None)
            if ts is None:
                continue
            if getattr(ts, "tzinfo", None) is None and created.tzinfo is not None:
                # naive candle times: keep relative order only
                after.append(candle)
                continue
            try:
                if ts >= created:
                    after.append(candle)
            except TypeError:
                after.append(candle)
        return after

    @staticmethod
    def _detect_path(
        *,
        signal: str,
        entry: float,
        sl: float,
        tp: float,
        candles: list,
    ) -> tuple[str, float, int]:
        for index, candle in enumerate(candles, start=1):
            high = float(candle.high)
            low = float(candle.low)
            close = float(candle.close)

            if signal == "BUY":
                # Conservative: SL before TP if both touched in same bar
                if sl and low <= sl:
                    return OutcomeResult.SL_HIT.value, sl, index
                if tp and high >= tp:
                    return OutcomeResult.TP_HIT.value, tp, index
            elif signal == "SELL":
                if sl and high >= sl:
                    return OutcomeResult.SL_HIT.value, sl, index
                if tp and low <= tp:
                    return OutcomeResult.TP_HIT.value, tp, index

        last_close = float(candles[-1].close)
        return OutcomeResult.TIMEOUT.value, last_close, len(candles)

    @staticmethod
    def _label_from_result(
        result: str,
        entry: float,
        exit_price: float,
        signal: str,
    ) -> str:
        if result == OutcomeResult.TP_HIT.value:
            return "WIN"
        if result == OutcomeResult.SL_HIT.value:
            return "LOSS"
        pnl = OutcomeTracker._signed_pnl(signal, entry, exit_price)
        if pnl > 0:
            return "WIN"
        if pnl < 0:
            return "LOSS"
        return "NEUTRAL"

    @staticmethod
    def _signed_pnl(signal: str, entry: float, exit_price: float) -> float:
        if signal == "BUY":
            return exit_price - entry
        if signal == "SELL":
            return entry - exit_price
        return 0.0

    @staticmethod
    def _duration_minutes(
        recommendation: Recommendation,
        candles: list,
        bars_held: int,
    ) -> int | None:
        created = getattr(recommendation, "created_at", None)
        if created is not None and bars_held > 0 and bars_held <= len(candles):
            end_candle = candles[bars_held - 1]
            end_ts = getattr(end_candle, "time", None)
            if end_ts is not None:
                try:
                    return max(0, int((end_ts - created).total_seconds() // 60))
                except TypeError:
                    pass
        # Fallback: approximate from timeframe minutes * bars
        tf = str(recommendation.timeframe).upper()
        minutes = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 60,
            "H4": 240,
            "D1": 1440,
            "DAILY": 1440,
        }.get(tf, 5)
        return bars_held * minutes
