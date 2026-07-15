"""
Athena Logging Middleware.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request and response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start = time.perf_counter()

        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000

        request_id = getattr(
            request.state,
            "request_id",
            "-",
        )

        logger.info(
            "[%s] %s %s -> %d (%.2f ms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response