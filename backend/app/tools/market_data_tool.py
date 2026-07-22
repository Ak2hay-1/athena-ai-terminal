"""
Market data tool — agents fetch candles via tools, not services.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from app.core.exceptions import ValidationException
from app.core.logger import get_logger
from app.database.database import SessionLocal
from app.services.market_service import MarketService
from app.tools.base import BaseTool

logger = get_logger("athena.tools.market_data")


def _serialize_candle(candle: Any) -> dict[str, Any]:
    time_value = candle.time
    if isinstance(time_value, datetime):
        time_iso = time_value.isoformat()
    else:
        time_iso = str(time_value)

    return {
        "time": time_iso,
        "open": float(candle.open),
        "high": float(candle.high),
        "low": float(candle.low),
        "close": float(candle.close),
        "tick_volume": int(candle.tick_volume),
        "spread": getattr(candle, "spread", None),
        "real_volume": getattr(candle, "real_volume", None),
    }


def _fetch_latest_candles(
    symbol: str,
    timeframe: str,
    limit: int,
) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        service = MarketService(db)
        candles = service.get_latest_candles(symbol, timeframe, limit=limit)
        return [_serialize_candle(c) for c in candles]
    finally:
        db.close()


def _fetch_latest(
    symbol: str,
    timeframe: str,
) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        service = MarketService(db)
        try:
            candle = service.get_latest(symbol, timeframe)
        except ValidationException:
            return None
        return _serialize_candle(candle)
    finally:
        db.close()


def _fetch_batch(
    symbols: list[str],
    timeframes: list[str],
    limit: int,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """
    Batch fetch: symbol -> timeframe -> candles (parallel per pair).
    """
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import as_completed

    result: dict[str, dict[str, list[dict[str, Any]]]] = {
        symbol: {} for symbol in symbols
    }
    pairs = [(s, tf) for s in symbols for tf in timeframes]
    if not pairs:
        return result

    def _one(symbol: str, timeframe: str) -> tuple[str, str, list[dict[str, Any]]]:
        db = SessionLocal()
        try:
            service = MarketService(db)
            candles = service.get_latest_candles(
                symbol,
                timeframe,
                limit=limit,
            )
            return symbol, timeframe, [_serialize_candle(c) for c in candles]
        except Exception:
            logger.exception(
                "market_data_tool action=batch symbol=%s timeframe=%s status=error",
                symbol,
                timeframe,
            )
            return symbol, timeframe, []
        finally:
            db.close()

    workers = min(8, len(pairs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_one, symbol, timeframe) for symbol, timeframe in pairs
        ]
        for fut in as_completed(futures):
            symbol, timeframe, candles = fut.result()
            result[symbol][timeframe] = candles
    return result


class MarketDataTool(BaseTool):
    """
    Read-only market candle access for agents.
    """

    id = "market_data"
    name = "Market Data Tool"
    description = "Fetch market candles from the database"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        action = str(kwargs.get("action", "get_latest_candles"))

        if action == "get_latest_candles":
            symbol = str(kwargs["symbol"]).upper()
            timeframe = str(kwargs["timeframe"]).upper()
            limit = int(kwargs.get("limit", 200))
            candles = await asyncio.to_thread(
                _fetch_latest_candles,
                symbol,
                timeframe,
                limit,
            )
            return {
                "status": "ok",
                "tool_id": self.id,
                "action": action,
                "symbol": symbol,
                "timeframe": timeframe,
                "count": len(candles),
                "candles": candles,
            }

        if action == "get_latest":
            symbol = str(kwargs["symbol"]).upper()
            timeframe = str(kwargs["timeframe"]).upper()
            candle = await asyncio.to_thread(
                _fetch_latest,
                symbol,
                timeframe,
            )
            return {
                "status": "ok" if candle else "empty",
                "tool_id": self.id,
                "action": action,
                "symbol": symbol,
                "timeframe": timeframe,
                "candle": candle,
            }

        if action == "batch_candles":
            symbols = [str(s).upper() for s in (kwargs.get("symbols") or [])]
            timeframes = [
                str(t).upper() for t in (kwargs.get("timeframes") or [])
            ]
            limit = int(kwargs.get("limit", 200))
            data = await asyncio.to_thread(
                _fetch_batch,
                symbols,
                timeframes,
                limit,
            )
            return {
                "status": "ok",
                "tool_id": self.id,
                "action": action,
                "data": data,
            }

        return {
            "status": "error",
            "tool_id": self.id,
            "error": f"unknown_action:{action}",
        }
