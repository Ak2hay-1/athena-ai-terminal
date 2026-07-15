"""
Athena Backtest Engine.

Replays historical market data through the Athena analysis
pipeline and simulates trading performance.
"""

from __future__ import annotations

import pandas as pd

from app.ai.recommendation_engine import recommendation_engine
from app.backtesting.performance_metrics import PerformanceMetrics
from app.core.logger import logger


class BacktestEngine:
    """
    Historical strategy tester.
    """

    def run(
        self,
        dataframe: pd.DataFrame,
        warmup: int = 200,
    ) -> dict:

        if len(dataframe) <= warmup:

            return {
                "success": False,
                "message": "Not enough candles.",
            }

        trades: list[dict] = []

        logger.info(
            "Starting backtest using %d candles.",
            len(dataframe),
        )

        for i in range(
            warmup,
            len(dataframe),
        ):

            candles = dataframe.iloc[: i + 1]

            recommendation = (
                recommendation_engine.analyze(
                    candles
                )
            )

            if recommendation.signal == "WAIT":

                continue

            entry = recommendation.entry

            stop_loss = recommendation.stop_loss

            take_profit = recommendation.take_profit

            current = dataframe.iloc[i]

            exit_price = current["close"]

            pnl = (
                exit_price - entry
                if recommendation.signal == "BUY"
                else entry - exit_price
            )

            trades.append(
                {
                    "signal": recommendation.signal,
                    "entry": entry,
                    "exit": exit_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "profit": pnl,
                    "confidence": recommendation.confidence,
                }
            )

        metrics = PerformanceMetrics().calculate(
            trades,
        )

        logger.info(
            "Backtest completed with %d trades.",
            len(trades),
        )

        return {
            "success": True,
            "trades": trades,
            "metrics": metrics,
        }


backtest_engine = BacktestEngine()