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

        # #region agent log
        if any(
            marker in path
            for marker in ("/docs", "/openapi", "/health", "/auth/login", "/auth/me")
        ):
            try:
                import json
                from pathlib import Path

                Path(__file__).resolve().parents[3].joinpath("debug-9c9447.log").open(
                    "a", encoding="utf-8"
                ).write(
                    json.dumps(
                        {
                            "sessionId": "9c9447",
                            "runId": "pre-fix",
                            "hypothesisId": "A",
                            "location": "logging_middleware.py:entry",
                            "message": "HTTP request entered ASGI middleware",
                            "data": {"method": method, "path": path},
                            "timestamp": int(time.time() * 1000),
                        }
                    )
                    + "\n"
                )
            except Exception:
                pass
        # #endregion

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
