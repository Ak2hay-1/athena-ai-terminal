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
from app.analysis.risk_engine import risk_engine
from app.core.logger import logger
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

            # -------------------------------------
            # Market Analysis
            # -------------------------------------

            analysis = market_analyzer.analyze(
                dataframe
            )

            prompt = prompt_builder.build(
                analysis
            )

            response = ollama_client.generate(
                prompt
            )

            logger.info("=" * 80)
            logger.info("RAW OLLAMA RESPONSE")
            logger.info(response)
            logger.info("=" * 80)

            recommendation = response_parser.parse(
                response
            )

            # -------------------------------------
            # Risk Engine
            # -------------------------------------

            latest = dataframe.iloc[-1]

            price = float(
                latest["close"]
            )

            atr = float(
                analysis["indicators"]["atr"]
            )

            levels = risk_engine.calculate(
                direction=recommendation.signal,
                entry=price,
                atr=atr,
            )

            recommendation.entry = levels.entry

            recommendation.stop_loss = (
                levels.stop_loss
            )

            recommendation.take_profit = (
                levels.take_profit
            )

            recommendation.risk_reward = (
                levels.risk_reward
            )

            recommendation.trend = (
                analysis["trend"][
                    "direction"
                ]
            )

            recommendation.confluence = (
                analysis["confluence"][
                    "score"
                ]
            )

            recommendation.symbol = symbol

            recommendation.timeframe = timeframe

            # -------------------------------------
            # Persist Recommendation
            # -------------------------------------

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
