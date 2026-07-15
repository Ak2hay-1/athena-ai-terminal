"""
MetaTrader 5 Service.

Business logic for MT5 operations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.core.logger import get_logger
from app.mt5.providers import connection
from app.mt5.providers import manager
from app.schemas.mt5 import (
    MT5AccountInfo,
    MT5ConnectionStatus,
    MT5LoginRequest,
    MT5LoginResponse,
    MT5LogoutResponse,
    MT5TerminalInfo,
    MT5VersionInfo,
)

logger = get_logger(__name__)


class MT5Service:
    """
    Business service for MetaTrader 5.
    """

    def __init__(self) -> None:
        self.connection = connection
        self.manager = manager

    # =====================================================
    # Connection
    # =====================================================

    def initialize(
        self,
        path: str | None = None,
    ) -> bool:
        """
        Initialize MT5 terminal.
        """

        return self.connection.initialize(
            path=path,
        )

    def shutdown(
        self,
    ) -> MT5LogoutResponse:
        """
        Shutdown MT5 terminal.
        """

        self.connection.shutdown()

        return MT5LogoutResponse(
            success=True,
            message="MT5 terminal shut down successfully.",
        )

    # =====================================================
    # Login
    # =====================================================

    def login(
        self,
        request: MT5LoginRequest,
    ) -> MT5LoginResponse:
        """
        Login to MT5 account.
        """

        self.connection.login(
            login=request.login,
            password=request.password,
            server=request.server,
            timeout=request.timeout,
        )

        account = self.get_account_info()

        logger.info(
            "Logged into MT5 account %s",
            request.login,
        )

        return MT5LoginResponse(
            success=True,
            message="Login successful.",
            account=account,
        )

    # =====================================================
    # Status
    # =====================================================

    def status(
        self,
    ) -> MT5ConnectionStatus:
        """
        Current connection status.
        """

        account = None

        if self.connection.connected:
            try:
                account = self.manager.account_info()
            except Exception:
                account = None

        return MT5ConnectionStatus(
            connected=self.connection.connected,
            initialized=self.connection.initialized,
            logged_in=self.connection.logged_in,
            server=getattr(account, "server", None),
            login=getattr(account, "login", None),
            message="Connected"
            if self.connection.connected
            else "Disconnected",
        )

    # =====================================================
    # Account
    # =====================================================

    def get_account_info(
        self,
    ) -> MT5AccountInfo:
        """
        Retrieve account information.
        """

        info = self.manager.account_info()

        return MT5AccountInfo(
            login=info.login,
            name=info.name,
            server=info.server,
            company=info.company,
            currency=info.currency,
            leverage=info.leverage,
            balance=Decimal(str(info.balance)),
            equity=Decimal(str(info.equity)),
            profit=Decimal(str(info.profit)),
            credit=Decimal(str(info.credit)),
            margin=Decimal(str(info.margin)),
            margin_free=Decimal(str(info.margin_free)),
            margin_level=Decimal(str(info.margin_level)),
            assets=Decimal(str(info.assets)),
            liabilities=Decimal(str(info.liabilities)),
            commission_blocked=Decimal(str(info.commission_blocked)),
            trade_allowed=info.trade_allowed,
            trade_expert=info.trade_expert,
            margin_mode=info.margin_mode,
            fifo_close=info.fifo_close,
            limit_orders=info.limit_orders,
            currency_digits=info.currency_digits,
            connected=True,
            timestamp=datetime.utcnow(),
        )

    # =====================================================
    # Terminal
    # =====================================================

    def get_terminal_info(
        self,
    ) -> MT5TerminalInfo:
        """
        Retrieve terminal information.
        """

        info = self.manager.terminal_info()

        return MT5TerminalInfo(
            company=info.company,
            name=info.name,
            language=info.language,
            path=info.path,
            data_path=info.data_path,
            commondata_path=info.commondata_path,
            community_account=info.community_account,
            community_connection=info.community_connection,
            connected=info.connected,
            trade_allowed=info.trade_allowed,
            tradeapi_disabled=info.tradeapi_disabled,
            dlls_allowed=info.dlls_allowed,
            email_enabled=info.email_enabled,
            ftp_enabled=info.ftp_enabled,
            notifications_enabled=info.notifications_enabled,
            mqid=info.mqid,
            build=info.build,
            maxbars=info.maxbars,
            ping_last=info.ping_last,
            codepage=info.codepage,
        )

    # =====================================================
    # Version
    # =====================================================

    def get_version(
        self,
    ) -> MT5VersionInfo:
        """
        Retrieve MT5 version.
        """

        version = self.manager.version()

        return MT5VersionInfo(
            version=version[0],
            build=version[1],
            release_date=str(version[2]),
        )


mt5_service = MT5Service()
