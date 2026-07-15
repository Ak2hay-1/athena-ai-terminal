"""
MetaTrader 5 Exceptions.

Custom exception hierarchy used throughout the MT5 module.
"""

from __future__ import annotations


class MT5Error(Exception):
    """
    Base exception for all MT5 errors.
    """

    def __init__(
        self,
        message: str,
    ) -> None:

        self.message = message

        super().__init__(message)


# ==========================================================
# Connection
# ==========================================================

class MT5InitializationError(MT5Error):
    """
    MT5 terminal initialization failed.
    """


class MT5ConnectionError(MT5Error):
    """
    Unable to connect to MT5 terminal.
    """


class MT5LoginError(MT5Error):
    """
    MT5 login failed.
    """


class MT5ShutdownError(MT5Error):
    """
    MT5 shutdown failed.
    """


class MT5TerminalNotRunningError(MT5Error):
    """
    MT5 terminal is not running.
    """


class MT5DisconnectedError(MT5Error):
    """
    MT5 connection lost.
    """


# ==========================================================
# Account
# ==========================================================

class MT5AccountError(MT5Error):
    """
    Account operation failed.
    """


class MT5UnauthorizedError(MT5Error):
    """
    Trading account is unauthorized.
    """


# ==========================================================
# Symbol
# ==========================================================

class MT5SymbolError(MT5Error):
    """
    Symbol related error.
    """


class MT5SymbolNotFoundError(MT5SymbolError):
    """
    Symbol does not exist.
    """


class MT5SymbolNotVisibleError(MT5SymbolError):
    """
    Symbol is hidden in Market Watch.
    """


# ==========================================================
# Market Data
# ==========================================================

class MT5TickError(MT5Error):
    """
    Tick retrieval failed.
    """


class MT5CandleError(MT5Error):
    """
    Candle retrieval failed.
    """


class MT5HistoryError(MT5Error):
    """
    Historical data retrieval failed.
    """


# ==========================================================
# Trading
# ==========================================================

class MT5TradeError(MT5Error):
    """
    Base trading error.
    """


class MT5OrderError(MT5TradeError):
    """
    Order execution failed.
    """


class MT5PositionError(MT5TradeError):
    """
    Position operation failed.
    """


class MT5ModifyOrderError(MT5TradeError):
    """
    Order modification failed.
    """


class MT5ClosePositionError(MT5TradeError):
    """
    Position close failed.
    """


class MT5CancelOrderError(MT5TradeError):
    """
    Pending order cancellation failed.
    """


# ==========================================================
# Validation
# ==========================================================

class MT5InvalidVolumeError(MT5TradeError):
    """
    Invalid trade volume.
    """


class MT5InvalidPriceError(MT5TradeError):
    """
    Invalid price.
    """


class MT5InvalidStopsError(MT5TradeError):
    """
    Invalid stop loss or take profit.
    """


class MT5InvalidExpirationError(MT5TradeError):
    """
    Invalid expiration.
    """


# ==========================================================
# Broker
# ==========================================================

class MT5InsufficientFundsError(MT5TradeError):
    """
    Insufficient account funds.
    """


class MT5MarketClosedError(MT5TradeError):
    """
    Market is closed.
    """


class MT5RequoteError(MT5TradeError):
    """
    Broker requested requote.
    """


class MT5PriceChangedError(MT5TradeError):
    """
    Price changed before execution.
    """


class MT5NoPriceError(MT5TradeError):
    """
    No market price available.
    """


class MT5TradeTimeoutError(MT5TradeError):
    """
    Trade request timed out.
    """


class MT5TradeDisabledError(MT5TradeError):
    """
    Trading disabled by broker.
    """


# ==========================================================
# Internal
# ==========================================================

class MT5MappingError(MT5Error):
    """
    Failed to map MT5 data.
    """


class MT5ConfigurationError(MT5Error):
    """
    MT5 configuration error.
    """


class MT5NotImplementedError(MT5Error):
    """
    Requested feature not implemented.
    """