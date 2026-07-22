"""
WebSocket notification channel (user-scoped).
"""

from __future__ import annotations

import time

from app.core.settings import settings
from app.notifications.message import DeliveryResult
from app.notifications.message import NotificationMessage
from app.websocket.connection_manager import connection_manager


class WebSocketChannel:
    name = "websocket"

    async def send(self, message: NotificationMessage) -> DeliveryResult:
        started = time.perf_counter()
        if not settings.NOTIFY_WEBSOCKET_ENABLED:
            return DeliveryResult(
                channel=self.name,
                status="skipped",
                error="websocket notifications disabled",
            )
        try:
            payload = {
                "type": "notification",
                "message_type": message.message_type,
                "priority": message.priority,
                "summary": message.summary,
                "confidence": message.confidence,
                "reasoning": message.reasoning,
                "risk": message.risk,
                "stop_loss": message.stop_loss,
                "take_profit": message.take_profit,
                "evidence": message.evidence,
                "action": message.action,
                "symbol": message.symbol,
                "side": message.side,
                "extra": message.extra,
            }
            sent = await connection_manager.send_to_user(message.user_id, payload)
            latency = (time.perf_counter() - started) * 1000
            if sent <= 0:
                return DeliveryResult(
                    channel=self.name,
                    status="skipped",
                    latency_ms=latency,
                    error="no active websocket for user",
                )
            return DeliveryResult(
                channel=self.name,
                status="sent",
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return DeliveryResult(
                channel=self.name,
                status="failed",
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )
