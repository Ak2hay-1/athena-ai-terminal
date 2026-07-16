"""
WebSocket broadcast helpers for market updates.
"""

from __future__ import annotations

import asyncio

from app.core.logger import logger
from app.websocket.connection_manager import connection_manager


def broadcast_candle_update(
    *,
    symbol: str,
    timeframe: str,
    inserted: int,
    recommendation=None,
) -> None:
    """
    Broadcast candle and recommendation updates to subscribers.
    """

    channel = f"{symbol.upper()}:{timeframe.upper()}"

    payload = {
        "type": "candle_update",
        "symbol": symbol.upper(),
        "timeframe": timeframe.upper(),
        "inserted": inserted,
        "channel": channel,
    }

    if recommendation is not None:

        payload["recommendation"] = {
            "signal": recommendation.signal,
            "confidence": recommendation.confidence,
            "entry": recommendation.entry,
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
        }

    try:

        loop = asyncio.get_event_loop()

        if loop.is_running():

            asyncio.create_task(
                connection_manager.broadcast_channel(
                    channel,
                    payload,
                )
            )

        else:

            loop.run_until_complete(
                connection_manager.broadcast_channel(
                    channel,
                    payload,
                )
            )

    except RuntimeError:

        asyncio.run(
            connection_manager.broadcast_channel(
                channel,
                payload,
            )
        )

    except Exception:

        logger.exception(
            "WebSocket broadcast failed for %s",
            channel,
        )
