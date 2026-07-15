"""
MetaTrader 5 Connection Service.

Business service responsible for the MT5 terminal lifecycle.
"""

from __future__ import annotations

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Connection

logger = get_logger(__name__)


class ConnectionService:
    """
    MT5 terminal lifecycle service.

    This service is responsible for:

    - Initializing the terminal
    - Shutting down the terminal
    - Connection health checks
    - Connection status

    It intentionally does NOT handle:

    - Login
    - Account information
    - Trading
    - Market data
    """

    def __init__(
        self,
        connection: IMT5Connection,
    ) -> None:
        self._connection = connection

    # =====================================================
    # Lifecycle
    # =====================================================

    def initialize(
        self,
        *,
        path: str | None = None,
        timeout: int = 60000,
        portable: bool = False,
    ) -> bool:
        """
        Initialize the MT5 terminal.
        """

        logger.info("Initializing MT5 terminal...")

        return self._connection.initialize(
            path=path,
            timeout=timeout,
            portable=portable,
        )

    def shutdown(self) -> None:
        """
        Shutdown the MT5 terminal.
        """

        logger.info("Shutting down MT5 terminal...")

        self._connection.shutdown()

    # =====================================================
    # Status
    # =====================================================

    @property
    def initialized(self) -> bool:
        """
        Whether the MT5 terminal has been initialized.
        """

        return self._connection.initialized

    @property
    def connected(self) -> bool:
        """
        Whether the MT5 terminal is connected.
        """

        return self._connection.connected

    def health(self) -> bool:
        """
        Perform a health check.
        """

        return self._connection.health_check()

    # =====================================================
    # Diagnostics
    # =====================================================

    def last_error(self) -> tuple[int, str]:
        """
        Return the last MT5 SDK error.
        """

        return self._connection.last_error()

    # =====================================================
    # Information
    # =====================================================

    def terminal_info(self):
        """
        Get terminal information.
        """

        return self._connection.terminal_info()

    def version(self):
        """
        Get MT5 terminal version.
        """

        return self._connection.version()
