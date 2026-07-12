"""
Custom exceptions used throughout the Athena application.
"""

from __future__ import annotations


class AthenaException(Exception):
    """Base exception for Athena."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ConfigurationException(AthenaException):
    """Raised when application configuration is invalid."""


class DatabaseException(AthenaException):
    """Raised when a database operation fails."""


class MarketException(AthenaException):
    """Raised when a market data operation fails."""


class MT5ConnectionException(MarketException):
    """Raised when MetaTrader 5 connection fails."""


class SymbolNotFoundException(MarketException):
    """Raised when a trading symbol cannot be found."""


class CandleDataException(MarketException):
    """Raised when candle data cannot be retrieved."""


class TickDataException(MarketException):
    """Raised when tick data cannot be retrieved."""


class IndicatorException(AthenaException):
    """Raised when indicator calculation fails."""


class PatternException(AthenaException):
    """Raised when pattern detection fails."""


class NewsException(AthenaException):
    """Raised when news processing fails."""


class AIException(AthenaException):
    """Raised when AI processing fails."""


class TradingException(AthenaException):
    """Raised when trading execution fails."""


class RiskException(AthenaException):
    """Raised when risk validation fails."""


class ValidationException(AthenaException):
    """Raised when request validation fails."""