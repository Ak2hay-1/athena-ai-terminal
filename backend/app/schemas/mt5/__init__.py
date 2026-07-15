"""
MetaTrader 5 Schemas.

This package contains all Pydantic schemas used by the
MT5 integration layer.
"""

# ==========================================================
# Account
# ==========================================================

from .account import (
    MT5AccountBase,
    MT5AccountInfo,
    MT5AccountSummary,
    MT5ConnectionStatus,
    MT5LoginRequest,
    MT5LoginResponse,
    MT5LogoutResponse,
)

# ==========================================================
# Terminal
# ==========================================================

from .terminal import (
    MT5InitializeRequest,
    MT5InitializeResponse,
    MT5ShutdownResponse,
    MT5TerminalHealth,
    MT5TerminalInfo,
    MT5TerminalStatus,
    MT5VersionInfo,
)

# ==========================================================
# Symbol
# ==========================================================

from .symbol import (
    MT5Quote,
    MT5SymbolInfo,
    MT5SymbolList,
    MT5SymbolSearchRequest,
    MT5SymbolSelectRequest,
    MT5SymbolSelectResponse,
    MT5SymbolSummary,
)

# ==========================================================
# Tick
# ==========================================================

from .tick import (
    MT5LiveTick,
    MT5SpreadInfo,
    MT5TickBatchRequest,
    MT5TickHistoryRequest,
    MT5TickHistoryResponse,
    MT5TickInfo,
    MT5TickRequest,
    MT5TickStatistics,
    MT5TickStream,
    MT5TickSubscription,
    MT5TickSubscriptionResponse,
)

# ==========================================================
# Candle
# ==========================================================

from .candle import (
    MT5BulkCandleImport,
    MT5Candle,
    MT5CandleRangeRequest,
    MT5CandleRequest,
    MT5CandleResponse,
    MT5CandleStatistics,
    MT5CandleSync,
    MT5CollectorStatus,
    MT5LatestCandle,
    MT5LiveCandle,
    MT5Timeframe,
)

# ==========================================================
# Order
# ==========================================================

from .order import (
    MT5CancelOrderRequest,
    MT5CloseOrderRequest,
    MT5ModifyOrderRequest,
    MT5OrderAction,
    MT5OrderFilling,
    MT5OrderInfo,
    MT5OrderList,
    MT5OrderRequest,
    MT5OrderResult,
    MT5OrderStatus,
    MT5OrderTime,
    MT5OrderType,
    MT5OrderValidation,
)

# ==========================================================
# Position
# ==========================================================

from .position import (
    MT5ClosePositionRequest,
    MT5ModifyPositionRequest,
    MT5PartialCloseRequest,
    MT5PositionFilter,
    MT5PositionInfo,
    MT5PositionList,
    MT5PositionResult,
    MT5PositionRisk,
    MT5PositionStatistics,
    MT5PositionSummary,
    MT5PositionType,
)

# ==========================================================
# History
# ==========================================================

from .history import (
    MT5DailyStatistics,
    MT5DealEntry,
    MT5DealInfo,
    MT5DealType,
    MT5EquityCurve,
    MT5EquityPoint,
    MT5HistoryExportRequest,
    MT5HistoryRequest,
    MT5HistoryResponse,
    MT5MonthlyStatistics,
    MT5OrderHistory,
    MT5ProfitSummary,
    MT5TradeAnalytics,
)

__all__ = [
    # ======================================================
    # Account
    # ======================================================
    "MT5AccountBase",
    "MT5AccountInfo",
    "MT5AccountSummary",
    "MT5ConnectionStatus",
    "MT5LoginRequest",
    "MT5LoginResponse",
    "MT5LogoutResponse",

    # ======================================================
    # Terminal
    # ======================================================
    "MT5InitializeRequest",
    "MT5InitializeResponse",
    "MT5ShutdownResponse",
    "MT5TerminalHealth",
    "MT5TerminalInfo",
    "MT5TerminalStatus",
    "MT5VersionInfo",

    # ======================================================
    # Symbol
    # ======================================================
    "MT5Quote",
    "MT5SymbolInfo",
    "MT5SymbolList",
    "MT5SymbolSearchRequest",
    "MT5SymbolSelectRequest",
    "MT5SymbolSelectResponse",
    "MT5SymbolSummary",

    # ======================================================
    # Tick
    # ======================================================
    "MT5LiveTick",
    "MT5SpreadInfo",
    "MT5TickBatchRequest",
    "MT5TickHistoryRequest",
    "MT5TickHistoryResponse",
    "MT5TickInfo",
    "MT5TickRequest",
    "MT5TickStatistics",
    "MT5TickStream",
    "MT5TickSubscription",
    "MT5TickSubscriptionResponse",

    # ======================================================
    # Candle
    # ======================================================
    "MT5BulkCandleImport",
    "MT5Candle",
    "MT5CandleRangeRequest",
    "MT5CandleRequest",
    "MT5CandleResponse",
    "MT5CandleStatistics",
    "MT5CandleSync",
    "MT5CollectorStatus",
    "MT5LatestCandle",
    "MT5LiveCandle",
    "MT5Timeframe",

    # ======================================================
    # Order
    # ======================================================
    "MT5CancelOrderRequest",
    "MT5CloseOrderRequest",
    "MT5ModifyOrderRequest",
    "MT5OrderAction",
    "MT5OrderFilling",
    "MT5OrderInfo",
    "MT5OrderList",
    "MT5OrderRequest",
    "MT5OrderResult",
    "MT5OrderStatus",
    "MT5OrderTime",
    "MT5OrderType",
    "MT5OrderValidation",

    # ======================================================
    # Position
    # ======================================================
    "MT5ClosePositionRequest",
    "MT5ModifyPositionRequest",
    "MT5PartialCloseRequest",
    "MT5PositionFilter",
    "MT5PositionInfo",
    "MT5PositionList",
    "MT5PositionResult",
    "MT5PositionRisk",
    "MT5PositionStatistics",
    "MT5PositionSummary",
    "MT5PositionType",

    # ======================================================
    # History
    # ======================================================
    "MT5DailyStatistics",
    "MT5DealEntry",
    "MT5DealInfo",
    "MT5DealType",
    "MT5EquityCurve",
    "MT5EquityPoint",
    "MT5HistoryExportRequest",
    "MT5HistoryRequest",
    "MT5HistoryResponse",
    "MT5MonthlyStatistics",
    "MT5OrderHistory",
    "MT5ProfitSummary",
    "MT5TradeAnalytics",
]