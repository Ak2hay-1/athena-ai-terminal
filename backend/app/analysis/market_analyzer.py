"""
Market Analyzer.

Central analysis engine.
"""

from __future__ import annotations

import pandas as pd

from app.analysis.market_structure_analyzer import (
    market_structure_analyzer,
)
from app.analysis.momentum_analyzer import (
    momentum_analyzer,
)
from app.analysis.trend_analyzer import (
    trend_analyzer,
)
from app.analysis.volatility_analyzer import (
    volatility_analyzer,
)
from app.indicators.indicator_engine import (
    indicator_engine,
)
from app.patterns.pattern_engine import (
    pattern_engine,
)


class MarketAnalyzer:

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict:

        if dataframe.empty:

            return {
                "status": "error",
                "message": "No market data.",
            }

        df = indicator_engine.calculate(dataframe)

        df = pattern_engine.detect(df)

        trend = trend_analyzer.analyze(df)

        momentum = momentum_analyzer.analyze(df)

        volatility = volatility_analyzer.analyze(df)

        structure = (
            market_structure_analyzer.analyze(df)
        )

        latest = df.iloc[-1]

        return {

            "symbol": dataframe.iloc[-1].get(
                "symbol",
                "UNKNOWN",
            ),

            "price": float(latest["close"]),

            "trend": trend,

            "momentum": momentum,

            "volatility": volatility,

            "market_structure": structure,
        }


market_analyzer = MarketAnalyzer()