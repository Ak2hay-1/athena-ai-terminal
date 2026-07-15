"""
Global Exception Handlers.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import AthenaException
from app.core.logger import logger


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register all application exception handlers.
    """

    @app.exception_handler(
        AthenaException,
    )
    async def athena_exception_handler(
        request: Request,
        exc: AthenaException,
    ):

        logger.error(
            "%s %s -> %s",
            request.method,
            request.url.path,
            exc.message,
        )

        return JSONResponse(

            status_code=exc.status_code,

            content={

                "success": False,

                "error": exc.message,

            },

        )

    @app.exception_handler(
        ValidationError,
    )
    async def validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ):

        logger.warning(
            "Validation failed: %s",
            exc,
        )

        return JSONResponse(

            status_code=422,

            content={

                "success": False,

                "error": "Validation failed.",

                "details": exc.errors(),

            },

        )

    @app.exception_handler(
        Exception,
    )
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):

        logger.exception(
            "Unhandled exception: %s",
            exc,
        )

        return JSONResponse(

            status_code=500,

            content={

                "success": False,

                "error": "Internal server error.",

            },

        )