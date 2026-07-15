"""
Athena Custom Exceptions.
"""

from __future__ import annotations


class AthenaException(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
    ) -> None:

        self.message = message
        self.status_code = status_code

        super().__init__(message)


class DatabaseException(AthenaException):
    """
    Database operation failed.
    """

    def __init__(
        self,
        message: str = "Database operation failed.",
    ) -> None:

        super().__init__(
            message,
            status_code=500,
        )


class MT5Exception(AthenaException):
    """
    MetaTrader error.
    """

    def __init__(
        self,
        message: str = "MetaTrader connection failed.",
    ) -> None:

        super().__init__(
            message,
            status_code=503,
        )


class AIException(AthenaException):
    """
    AI processing failed.
    """

    def __init__(
        self,
        message: str = "AI processing failed.",
    ) -> None:

        super().__init__(
            message,
            status_code=500,
        )


class ValidationException(AthenaException):
    """
    Business validation failed.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        super().__init__(
            message,
            status_code=400,
        )


class TradingException(AthenaException):
    """
    Trading execution failed.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        super().__init__(
            message,
            status_code=500,
        )