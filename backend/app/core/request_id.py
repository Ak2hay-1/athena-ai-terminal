"""
Athena Request ID Middleware.

Adds a unique request ID to every incoming HTTP request.
Uses pure ASGI so WebSocket upgrades are not broken by BaseHTTPMiddleware.
"""

from __future__ import annotations

from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """
    Adds a unique request ID to every HTTP request.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (REQUEST_ID_HEADER.lower().encode(), request_id.encode()),
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)
