"""
WebSocket broadcast helpers for market updates.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logger import logger
from app.websocket.connection_manager import connection_manager

_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Capture the FastAPI/uvicorn event loop for thread-safe broadcasts."""
    global _main_loop
    _main_loop = loop


def broadcast_candle_update(
    *,
    symbol: str,
    timeframe: str,
    inserted: int,
    recommendation=None,
    candle: Any = None,
) -> None:
    """
    Broadcast candle and recommendation updates to subscribers.

    Safe to call from APScheduler background threads.
    """

    channel = f"{symbol.upper()}:{timeframe.upper()}"

    payload: dict[str, Any] = {
        "type": "candle_update",
        "symbol": symbol.upper(),
        "timeframe": timeframe.upper(),
        "inserted": inserted,
        "channel": channel,
    }

    if candle is not None:
        try:
            if hasattr(candle, "model_dump"):
                payload["candle"] = candle.model_dump(mode="json")
            elif isinstance(candle, dict):
                payload["candle"] = candle
            else:
                payload["candle"] = {
                    "symbol": getattr(candle, "symbol", symbol),
                    "timeframe": getattr(candle, "timeframe", timeframe),
                    "time": str(getattr(candle, "time", "")),
                    "open": float(getattr(candle, "open", 0)),
                    "high": float(getattr(candle, "high", 0)),
                    "low": float(getattr(candle, "low", 0)),
                    "close": float(getattr(candle, "close", 0)),
                    "tick_volume": int(getattr(candle, "tick_volume", 0) or 0),
                }
        except Exception:
            logger.exception(
                "Failed to serialize candle for %s",
                channel,
            )

    if recommendation is not None:
        signal = recommendation.signal
        if hasattr(signal, "value"):
            signal = signal.value
        payload["recommendation"] = {
            "signal": signal,
            "confidence": recommendation.confidence,
            "entry": recommendation.entry,
            "entry_type": getattr(recommendation, "entry_type", "NONE"),
            "stop_loss": recommendation.stop_loss,
            "take_profit": recommendation.take_profit,
            "risk_reward": getattr(recommendation, "risk_reward", 0),
            "risk_pips": getattr(recommendation, "risk_pips", 0),
            "reward_pips": getattr(recommendation, "reward_pips", 0),
            "sl_reason": getattr(recommendation, "sl_reason", ""),
            "tp_reason": getattr(recommendation, "tp_reason", ""),
            "validation": getattr(recommendation, "validation", {}) or {},
            "trend": getattr(recommendation, "trend", None),
            "symbol": getattr(recommendation, "symbol", None),
            "timeframe": getattr(recommendation, "timeframe", None),
        }

    coro = connection_manager.broadcast_channel(channel, payload)

    try:
        loop = _main_loop
        if loop is None or loop.is_closed():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, loop)
            return

        if loop is not None and not loop.is_closed():
            loop.run_until_complete(coro)
            return

        asyncio.run(coro)

    except Exception:
        logger.exception(
            "WebSocket broadcast failed for %s",
            channel,
        )
