"""
Trading Engine Exceptions.

Custom exceptions used throughout the Athena Trading Engine.
"""

from __future__ import annotations


class TradingError(Exception):
    """
    Base exception for all trading errors.
    """

    def __init__(
        self,
        message: str,
    ) -> None:
        self.message = message
        super().__init__(message)


# ==========================================================
# Validation
# ==========================================================

class TradeValidationError(TradingError):
    """
    Invalid trade request.
    """


class InvalidSymbolError(TradeValidationError):
    """
    Invalid trading symbol.
    """


class InvalidVolumeError(TradeValidationError):
    """
    Invalid trade volume.
    """


class InvalidPriceError(TradeValidationError):
    """
    Invalid trade price.
    """


class InvalidStopLossError(TradeValidationError):
    """
    Invalid stop-loss.
    """


class InvalidTakeProfitError(TradeValidationError):
    """
    Invalid take-profit.
    """


class InvalidRiskError(TradeValidationError):
    """
    Invalid risk configuration.
    """


# ==========================================================
# Trading
# ==========================================================

class TradeExecutionError(TradingError):
    """
    Trade execution failed.
    """


class OrderPlacementError(TradeExecutionError):
    """
    Unable to place order.
    """


class OrderModificationError(TradeExecutionError):
    """
    Unable to modify order.
    """


class OrderCancellationError(TradeExecutionError):
    """
    Unable to cancel order.
    """


class PositionCloseError(TradeExecutionError):
    """
    Unable to close position.
    """


class PartialCloseError(TradeExecutionError):
    """
    Partial close failed.
    """


# ==========================================================
# Risk
# ==========================================================

class RiskManagementError(TradingError):
    """
    Risk engine error.
    """


class RiskLimitExceededError(RiskManagementError):
    """
    Maximum allowed risk exceeded.
    """


class MaximumTradesExceededError(RiskManagementError):
    """
    Too many open trades.
    """


class MaximumSymbolTradesExceededError(RiskManagementError):
    """
    Too many open trades for the same symbol.
    """


class MarginError(RiskManagementError):
    """
    Insufficient margin.
    """


# ==========================================================
# Position
# ==========================================================

class PositionError(TradingError):
    """
    Position operation failed.
    """


class PositionNotFoundError(PositionError):
    """
    Position does not exist.
    """


class PositionAlreadyClosedError(PositionError):
    """
    Position already closed.
    """


# ==========================================================
# Strategy
# ==========================================================

class StrategyError(TradingError):
    """
    Trading strategy error.
    """


class SignalRejectedError(StrategyError):
    """
    Strategy signal rejected.
    """


class DuplicateSignalError(StrategyError):
    """
    Duplicate trading signal.
    """


# ==========================================================
# Market
# ==========================================================

class MarketClosedError(TradingError):
    """
    Market is currently closed.
    """


class MarketDataUnavailableError(TradingError):
    """
    Required market data unavailable.
    """


class SpreadTooHighError(TradingError):
    """
    Spread exceeds configured limit.
    """


class SlippageExceededError(TradingError):
    """
    Maximum slippage exceeded.
    """


# ==========================================================
# Broker
# ==========================================================

class BrokerError(TradingError):
    """
    Broker returned an error.
    """


class BrokerConnectionError(BrokerError):
    """
    Broker connection failed.
    """


class BrokerRejectedOrderError(BrokerError):
    """
    Broker rejected order.
    """


# ==========================================================
# Configuration
# ==========================================================

class TradingConfigurationError(TradingError):
    """
    Invalid trading configuration.
    """


class TradingEngineNotInitializedError(TradingError):
    """
    Trading engine not initialized.
    """