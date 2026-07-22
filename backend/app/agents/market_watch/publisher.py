"""
Market Watch event publisher with duplicate prevention.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from app.core.logger import get_logger
from app.events.publisher import EventPublisher
from app.events.types import EventType

logger = get_logger("athena.agents.market_watch")


class MarketWatchPublisher:
    """
    Publishes MarketUpdated events; skips duplicate detection keys.
    """

    def __init__(
        self,
        publisher: EventPublisher,
        *,
        max_dedup_keys: int = 5000,
    ) -> None:
        self._publisher = publisher
        self._max_dedup_keys = max_dedup_keys
        self._seen: OrderedDict[str, None] = OrderedDict()
        self.events_published = 0
        self.duplicates_skipped = 0

    def _dedup_key(
        self,
        symbol: str,
        timeframe: str,
        change_type: str,
        candle_time: str,
    ) -> str:
        return f"{symbol}|{timeframe}|{change_type}|{candle_time}"

    def was_published(
        self,
        symbol: str,
        timeframe: str,
        change_type: str,
        candle_time: str,
    ) -> bool:
        key = self._dedup_key(symbol, timeframe, change_type, candle_time)
        return key in self._seen

    def mark_published(
        self,
        symbol: str,
        timeframe: str,
        change_type: str,
        candle_time: str,
    ) -> None:
        key = self._dedup_key(symbol, timeframe, change_type, candle_time)
        self._seen[key] = None
        self._seen.move_to_end(key)
        while len(self._seen) > self._max_dedup_keys:
            self._seen.popitem(last=False)

    async def publish_change(self, change: dict[str, Any]) -> bool:
        symbol = str(change["symbol"])
        timeframe = str(change["timeframe"])
        change_type = str(change["change_type"])
        candle_time = str(change["timestamp"])

        if self.was_published(symbol, timeframe, change_type, candle_time):
            self.duplicates_skipped += 1
            logger.info(
                "market_watch action=dedup_skip symbol=%s timeframe=%s "
                "reason=%s candle_time=%s",
                symbol,
                timeframe,
                change_type,
                candle_time,
            )
            return False

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": change.get("price"),
            "timestamp": candle_time,
            "market_state": change.get("market_state") or {},
            "previous_state": change.get("previous_state") or {},
            "reason": change_type,
            "change_type": change_type,
            **{
                k: v
                for k, v in change.items()
                if k
                not in {
                    "symbol",
                    "timeframe",
                    "price",
                    "timestamp",
                    "market_state",
                    "previous_state",
                    "change_type",
                }
            },
        }

        await self._publisher.publish(
            EventType.MARKET_UPDATED,
            source="market_watch",
            payload=payload,
            correlation_id=f"{symbol}:{timeframe}:{candle_time}",
        )
        self.mark_published(symbol, timeframe, change_type, candle_time)
        self.events_published += 1

        try:
            from app.services.scanner_state import scanner_state
            from app.services.websocket_broadcast import broadcast_scanner_update

            event = scanner_state.record_market_watch(
                symbol=symbol,
                timeframe=timeframe,
                change_type=change_type,
                price=float(change["price"])
                if change.get("price") is not None
                else None,
                extras={
                    k: v
                    for k, v in change.items()
                    if k
                    not in {
                        "symbol",
                        "timeframe",
                        "price",
                        "timestamp",
                        "market_state",
                        "previous_state",
                        "change_type",
                    }
                },
            )
            broadcast_scanner_update(
                symbol=symbol,
                timeframe=timeframe,
                change_type=change_type,
                price=float(change["price"])
                if change.get("price") is not None
                else None,
                opportunity={
                    "market_watch_tag": change_type,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "weight": getattr(event, "weight", None) if event else None,
                },
            )
        except Exception:
            logger.exception(
                "market_watch action=scanner_broadcast_failed symbol=%s timeframe=%s",
                symbol,
                timeframe,
            )

        return True
