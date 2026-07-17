"""
Athena Recommendation Engine.

Risk engine owns signal, confidence, and all trade levels.
The LLM only explains the frozen plan.
"""

from __future__ import annotations

import pandas as pd

from app.ai.models import AIRecommendation
from app.ai.schemas.context import MarketContext
from app.ai.services.ai_service import ai_service
from app.analysis.market_analyzer import market_analyzer
from app.analysis.multi_timeframe_analyzer import multi_timeframe_analyzer
from app.core.enums import RecommendationSignal
from app.core.logger import logger
from app.repositories.recommendation_repository import RecommendationRepository
from app.risk.models import TradePlan
from app.risk.risk_engine import risk_engine


class RecommendationEngine:
    """
    AI Recommendation Engine.
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
        symbol: str,
        timeframe: str,
        repository: RecommendationRepository | None = None,
        *,
        news_context: dict | None = None,
        higher_timeframes: dict[str, pd.DataFrame] | None = None,
        weights: dict[str, float] | None = None,
    ) -> AIRecommendation:

        try:

            if dataframe.empty:

                return AIRecommendation(
                    signal=RecommendationSignal.NO_TRADE,
                    confidence=0,
                    reason=[
                        "No candle data available.",
                    ],
                    symbol=symbol,
                    timeframe=timeframe,
                )

            multi_tf = None
            multi_tf_trend = None

            if higher_timeframes:

                multi_tf = multi_timeframe_analyzer.analyze(
                    higher_timeframes,
                )
                multi_tf_trend = multi_tf.get("overall_trend")

            analysis = market_analyzer.analyze(
                dataframe,
                news_context=news_context,
                multi_timeframe=multi_tf,
                weights=weights,
            )

            plan = risk_engine.build_plan(
                dataframe,
                symbol=symbol,
                timeframe=timeframe,
                higher_timeframes=higher_timeframes,
                news_context=news_context,
                multi_tf_trend=multi_tf_trend,
            )

            recommendation = self._from_plan(
                plan,
                analysis=analysis,
                symbol=symbol,
                timeframe=timeframe,
            )

            trade_plan_payload = plan.model_dump()

            try:
                context = MarketContext.from_analysis(
                    analysis,
                    symbol=symbol,
                    timeframe=timeframe,
                    trade_plan=trade_plan_payload,
                )
                explanation = ai_service.generate_trade_explanation(context)
                if explanation.reasons:
                    recommendation.reason = [
                        *recommendation.reason,
                        *explanation.reasons,
                    ]
            except Exception as exc:
                logger.warning("AI explanation skipped: %s", exc)
                if not recommendation.reason:
                    recommendation.reason = [
                        plan.sl_reason or "Risk engine plan generated.",
                        plan.tp_reason or "",
                    ]

            if repository is not None:

                repository.create_recommendation(
                    recommendation=recommendation,
                    analysis={
                        **analysis,
                        "trade_plan": trade_plan_payload,
                    },
                )

            return recommendation

        except Exception as exc:

            logger.exception(exc)

            return AIRecommendation(
                signal=RecommendationSignal.NO_TRADE,
                confidence=0,
                reason=[
                    str(exc),
                ],
                symbol=symbol,
                timeframe=timeframe,
            )

    def _from_plan(
        self,
        plan: TradePlan,
        *,
        analysis: dict,
        symbol: str,
        timeframe: str,
    ) -> AIRecommendation:
        signal = plan.signal
        try:
            signal_enum = RecommendationSignal(signal)
        except ValueError:
            signal_enum = RecommendationSignal.NO_TRADE

        reasons = list(plan.reasons)
        if plan.sl_reason:
            reasons.append(plan.sl_reason)
        if plan.tp_reason:
            reasons.append(plan.tp_reason)
        if plan.entry_reason:
            reasons.append(plan.entry_reason)

        return AIRecommendation(
            signal=signal_enum,
            confidence=int(plan.confidence),
            entry=float(plan.entry),
            entry_type=plan.entry_type.value if hasattr(plan.entry_type, "value") else str(plan.entry_type),
            stop_loss=float(plan.stop_loss),
            take_profit=float(plan.take_profit),
            risk_reward=float(plan.risk_reward),
            risk_pips=float(plan.risk_pips),
            reward_pips=float(plan.reward_pips),
            sl_reason=plan.sl_reason,
            tp_reason=plan.tp_reason,
            entry_reason=plan.entry_reason,
            validation=plan.validation.model_dump(),
            reason=reasons,
            trend=plan.trend or analysis.get("trend", {}).get("direction"),
            confluence=analysis.get("confluence", {}).get("score"),
            symbol=symbol,
            timeframe=timeframe,
        )


recommendation_engine = RecommendationEngine()
