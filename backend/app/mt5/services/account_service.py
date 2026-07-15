"""
MetaTrader 5 Account Service.

Provides account and terminal information.
"""

from __future__ import annotations

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Manager
from app.mt5.mappers import MT5Mapper
from app.schemas.mt5 import (
    MT5AccountInfo,
    MT5TerminalInfo,
    MT5VersionInfo,
)

logger = get_logger(__name__)


class AccountService:
    """
    MT5 account service.

    Responsibilities
    ----------------
    - Account information
    - Terminal information
    - Version information

    This service intentionally does NOT handle:

    - Authentication
    - Orders
    - Positions
    - Market data
    """

    def __init__(
        self,
        manager: IMT5Manager,
    ) -> None:
        self._manager = manager

    # =====================================================
    # Account
    # =====================================================

    def account(self) -> MT5AccountInfo:
        """
        Get account information.
        """

        logger.debug(
            "Retrieving MT5 account information."
        )

        info = self._manager.account_info()

        return MT5Mapper.account(info)

    # =====================================================
    # Terminal
    # =====================================================

    def terminal(self) -> MT5TerminalInfo:
        """
        Get terminal information.
        """

        logger.debug(
            "Retrieving MT5 terminal information."
        )

        info = self._manager.terminal_info()

        return MT5Mapper.terminal(info)

    # =====================================================
    # Version
    # =====================================================

    def version(self) -> MT5VersionInfo:
        """
        Get terminal version.
        """

        logger.debug(
            "Retrieving MT5 version."
        )

        version = self._manager.version()

        return MT5Mapper.version(version)

    # =====================================================
    # Health
    # =====================================================

    def ping(self) -> bool:
        """
        Verify MT5 connectivity.

        Returns
        -------
        bool
            True if terminal responds.
        """

        try:
            self._manager.version()

            return True

        except Exception:
            return False
