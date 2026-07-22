"""
Athena Logging Middleware.

Uses pure ASGI so WebSocket upgrades are not broken by BaseHTTPMiddleware.
"""

from __future__ import annotations

import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logger import logger


class LoggingMiddleware:
    """
    Logs every HTTP request and response.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        method = scope.get("method", "-")
        path = scope.get("path", "-")
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 500))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = (time.perf_counter() - start) * 1000
            state = scope.get("state") or {}
            request_id = state.get("request_id", "-")
            logger.info(
                "[%s] %s %s -> %d (%.2f ms)",
                request_id,
                method,
                path,
                status_code,
                duration,
            )
