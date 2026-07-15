"""
Athena Market Stream.
"""

from __future__ import annotations

from app.websocket.connection_manager import (
    connection_manager,
)


class MarketStream:
    """
    Broadcasts market updates.

    Used by:

    • Collector
    • AI Engine
    • Trading Engine
    """

    async def publish_candle(

        self,

        symbol: str,

        candle: dict,

    ):

        await connection_manager.broadcast_symbol(

            symbol,

            {

                "type": "candle",

                "symbol": symbol,

                "data": candle,

            },

        )

    # -------------------------------------------------

    async def publish_analysis(

        self,

        symbol: str,

        analysis: dict,

    ):

        await connection_manager.broadcast_symbol(

            symbol,

            {

                "type": "analysis",

                "symbol": symbol,

                "data": analysis,

            },

        )

    # -------------------------------------------------

    async def publish_recommendation(

        self,

        symbol: str,

        recommendation: dict,

    ):

        await connection_manager.broadcast_symbol(

            symbol,

            {

                "type": "recommendation",

                "symbol": symbol,

                "data": recommendation,

            },

        )

    # -------------------------------------------------

    async def publish_portfolio(

        self,

        portfolio: dict,

    ):

        await connection_manager.broadcast(

            {

                "type": "portfolio",

                "data": portfolio,

            }

        )


market_stream = MarketStream()