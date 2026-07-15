"""
MetaTrader 5 Service Facade.

Public entry point for the MT5 module.
"""

from __future__ import annotations

from app.mt5.providers import (
    connection,
    manager,
)

from .account_service import AccountService
from .authentication_service import AuthenticationService
from .connection_service import ConnectionService
from .history_service import HistoryService
from .market_service import MarketService
from .trading_service import TradingService


class MT5Service:
    """
    Facade for all MT5 services.

    This is the only MT5 class that should be used
    outside the MT5 package.
    """

    def __init__(self) -> None:
        self.connection = ConnectionService(connection)
        self.authentication = AuthenticationService(manager)
        self.account = AccountService(manager)
        self.market = MarketService(manager)
        self.trading = TradingService(manager)
        self.history = HistoryService(manager)


# ==========================================================
# Singleton
# ==========================================================

mt5_service = MT5Service()
