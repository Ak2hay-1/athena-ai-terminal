"""
MetaTrader 5 custom exceptions.
"""

from __future__ import annotations


class MT5Error(Exception):
    """Base MT5 exception."""


class MT5ConnectionError(MT5Error):
    """Connection error."""


class MT5InitializationError(MT5ConnectionError):
    """Initialization failed."""


class MT5ShutdownError(MT5ConnectionError):
    """Shutdown failed."""


class MT5LoginError(MT5ConnectionError):
    """Login failed."""


class MT5AccountError(MT5Error):
    """Account operation failed."""


class MT5SymbolError(MT5Error):
    """Symbol operation failed."""


class MT5TickError(MT5Error):
    """Tick operation failed."""


class MT5CandleError(MT5Error):
    """Candle retrieval failed."""


class MT5OrderError(MT5Error):
    """Order operation failed."""


class MT5PositionError(MT5Error):
    """Position operation failed."""


class MT5HistoryError(MT5Error):
    """History retrieval failed."""
