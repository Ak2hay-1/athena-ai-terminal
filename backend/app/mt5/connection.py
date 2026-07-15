"""
MetaTrader 5 Connection.

Responsible only for managing the MT5 terminal lifecycle.
"""

from __future__ import annotations

from typing import Any

import MetaTrader5 as mt5

from app.core.logger import get_logger
from app.mt5.constants import DEFAULT_TIMEOUT
from app.mt5.exceptions import (
    MT5ConnectionError,
    MT5InitializationError,
    MT5ShutdownError,
)
from app.mt5.interfaces import IMT5Connection

logger = get_logger(__name__)


class MT5Connection(IMT5Connection):
    """
    MetaTrader 5 terminal lifecycle manager.

    Responsibilities:
        - Initialize terminal
        - Shutdown terminal
        - Health checks
        - Terminal information
        - Version information

    This class intentionally does NOT perform:

        - Login
        - Account operations
        - Orders
        - Positions
        - Market data
    """

    def __init__(self) -> None:
        self._initialized = False

    # =====================================================
    # Lifecycle
    # =====================================================

    def initialize(
        self,
        *,
        path: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        portable: bool = False,
    ) -> bool:
        """
        Initialize the MetaTrader 5 terminal.
        """

        if self._initialized:
            logger.debug("MT5 terminal already initialized.")
            return True

        logger.info("Initializing MetaTrader 5 terminal...")

        success = mt5.initialize(
            path=path,
            timeout=timeout,
            portable=portable,
        )

        if not success:
            error = mt5.last_error()

            logger.error(
                "Failed to initialize MT5 terminal: %s",
                error,
            )

            raise MT5InitializationError(str(error))

        self._initialized = True

        logger.info("MetaTrader 5 terminal initialized successfully.")

        return True

    def shutdown(self) -> None:
        """
        Shutdown the MT5 terminal.
        """

        if not self._initialized:
            logger.debug("MT5 terminal already shut down.")
            return

        logger.info("Shutting down MetaTrader 5 terminal...")

        try:
            mt5.shutdown()

            self._initialized = False

            logger.info("MetaTrader 5 terminal shut down successfully.")

        except Exception as exc:
            logger.exception("Error shutting down MT5 terminal.")

            raise MT5ShutdownError(str(exc)) from exc

    # =====================================================
    # Status
    # =====================================================

    @property
    def initialized(self) -> bool:
        """
        Whether the terminal has been initialized.
        """

        return self._initialized

    @property
    def connected(self) -> bool:
        """
        Whether the MT5 terminal is connected.
        """

        if not self._initialized:
            return False

        try:
            return mt5.terminal_info() is not None

        except Exception:
            return False

    # =====================================================
    # Terminal Information
    # =====================================================

    def terminal_info(self) -> Any:
        """
        Retrieve terminal information.
        """

        self._ensure_connected()

        info = mt5.terminal_info()

        if info is None:
            raise MT5ConnectionError(
                "Unable to retrieve terminal information."
            )

        return info

    def version(self) -> tuple[int, int, str]:
        """
        Retrieve MetaTrader 5 version.
        """

        self._ensure_connected()

        version = mt5.version()

        if version is None:
            raise MT5ConnectionError(
                "Unable to retrieve terminal version."
            )

        return version

    # =====================================================
    # Diagnostics
    # =====================================================

    def health_check(self) -> bool:
        """
        Verify terminal health.
        """

        if not self.connected:
            return False

        try:
            return mt5.version() is not None

        except Exception:
            return False

    def last_error(self) -> tuple[int, str]:
        """
        Return the last MT5 SDK error.
        """

        return mt5.last_error()

    # =====================================================
    # Helpers
    # =====================================================

    def _ensure_connected(self) -> None:
        """
        Ensure terminal is initialized and connected.
        """

        if not self.connected:
            raise MT5ConnectionError(
                "MetaTrader 5 terminal is not connected."
            )


