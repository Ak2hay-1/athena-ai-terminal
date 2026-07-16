"""
Athena Recommendation Engine.
"""

from __future__ import annotations

import pandas as pd

from app.ai.client import ollama_client
from app.ai.models import AIRecommendation
from app.ai.prompt_builder import prompt_builder
from app.ai.response_parser import response_parser
from app.analysis.market_analyzer import market_analyzer
from app.analysis.multi_timeframe_analyzer import multi_timeframe_analyzer
from app.analysis.risk_engine import risk_engine
from app.analysis.trade_validator import trade_validator
from app.core.logger import logger
from app.core.settings import settings
from app.repositories.recommendation_repository import RecommendationRepository


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
                    signal="HOLD",
                    confidence=0,
                    reason=[
                        "No candle data available."
                    ],
                )

            multi_tf = None

            if higher_timeframes:

                multi_tf = multi_timeframe_analyzer.analyze(
                    higher_timeframes,
                )

            analysis = market_analyzer.analyze(
                dataframe,
                news_context=news_context,
                multi_timeframe=multi_tf,
                weights=weights,
            )

            prompt = prompt_builder.build(
                analysis
            )

            response = ollama_client.generate(
                prompt
            )

            recommendation = response_parser.parse(
                response
            )

            if news_context and news_context.get("high_impact_upcoming"):

                if recommendation.signal in ("BUY", "SELL"):
                    recommendation.signal = "HOLD"
                    recommendation.confidence = min(
                        recommendation.confidence,
                        40,
                    )
                    recommendation.reason.append(
                        "Downgraded due to high-impact news window."
                    )

            latest = dataframe.iloc[-1]

            price = float(latest["close"])

            atr = float(
                analysis["indicators"]["atr"]
            )

            levels = risk_engine.calculate(
                direction=recommendation.signal,
                entry=price,
                atr=atr,
            )

            recommendation.entry = levels.entry
            recommendation.stop_loss = levels.stop_loss
            recommendation.take_profit = levels.take_profit
            recommendation.risk_reward = levels.risk_reward
            recommendation.trend = analysis["trend"]["direction"]
            recommendation.confluence = analysis["confluence"]["score"]
            recommendation.symbol = symbol
            recommendation.timeframe = timeframe

            validation = trade_validator.validate(
                recommendation,
                news_context=news_context,
            )

            if not validation.execute and recommendation.signal in ("BUY", "SELL"):
                recommendation.signal = "HOLD"
                recommendation.reason.extend(validation.reasons)

            if repository is not None:

                repository.create_recommendation(
                    recommendation=recommendation,
                    analysis=analysis,
                )

            return recommendation

        except Exception as exc:

            logger.exception(exc)

            return AIRecommendation(
                signal="HOLD",
                confidence=0,
                reason=[
                    str(exc),
                ],
            )


recommendation_engine = RecommendationEngine()
