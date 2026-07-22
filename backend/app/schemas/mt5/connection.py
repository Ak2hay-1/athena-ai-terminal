"""
MetaTrader 5 Connection Manager.
"""

from __future__ import annotations

import threading
from typing import Any

from app.mt5.sdk import mt5

from app.core.logger import get_logger
from app.mt5.constants import DEFAULT_TIMEOUT
from app.mt5.exceptions import (
    MT5ConnectionError,
    MT5InitializationError,
    MT5LoginError,
    MT5ShutdownError,
)

logger = get_logger(__name__)


class MT5Connection:
    """
    Thread-safe singleton wrapper around MetaTrader5.
    """

    _instance: "MT5Connection | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "MT5Connection":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:

        if getattr(self, "_initialized_object", False):
            return

        self._initialized_object = True

        self._lock = threading.RLock()

        self._initialized = False

        self._logged_in = False

    # =====================================================
    # Initialize
    # =====================================================

    def initialize(
        self,
        path: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        portable: bool = False,
    ) -> bool:
        """
        Initialize MetaTrader5 terminal.
        """

        with self._lock:

            if self._initialized:
                return True

            success = mt5.initialize(
                path=path,
                timeout=timeout,
                portable=portable,
            )

            if not success:

                error = mt5.last_error()

                raise MT5InitializationError(
                    f"Failed to initialize MT5: {error}"
                )

            self._initialized = True

            logger.info("MT5 initialized successfully.")

            return True

    # =====================================================
    # Login
    # =====================================================

    def login(
        self,
        login: int,
        password: str,
        server: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """
        Login to MT5 account.
        """

        with self._lock:

            if not self._initialized:
                self.initialize()

            success = mt5.login(
                login=login,
                password=password,
                server=server,
                timeout=timeout,
            )

            if not success:

                error = mt5.last_error()

                raise MT5LoginError(
                    f"MT5 login failed: {error}"
                )

            self._logged_in = True

            logger.info(
                "Logged into MT5 account %s",
                login,
            )

            return True

    # =====================================================
    # Shutdown
    # =====================================================

    def shutdown(self) -> None:
        """
        Shutdown MetaTrader5.
        """

        with self._lock:

            try:
                mt5.shutdown()

                self._initialized = False

                self._logged_in = False

                logger.info("MT5 shutdown complete.")

            except Exception as exc:
                raise MT5ShutdownError(
                    str(exc),
                ) from exc

    # =====================================================
    # Status
    # =====================================================

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def connected(self) -> bool:
        """
        Check whether MT5 is connected.
        """

        if not self._initialized:
            return False

        info = mt5.terminal_info()

        return info is not None

    # =====================================================
    # Info
    # =====================================================

    def version(self) -> tuple[int, int, str]:
        """
        Terminal version.
        """

        if not self.connected:
            raise MT5ConnectionError(
                "MT5 is not connected."
            )

        version = mt5.version()

        if version is None:
            raise MT5ConnectionError(
                "Unable to retrieve MT5 version."
            )

        return version

    def terminal_info(self) -> Any:
        """
        Return MT5 terminal information.
        """

        if not self.connected:
            raise MT5ConnectionError(
                "MT5 is not connected."
            )

        info = mt5.terminal_info()

        if info is None:
            raise MT5ConnectionError(
                "Unable to retrieve terminal information."
            )

        return info

    def account_info(self) -> Any:
        """
        Return account information.
        """

        if not self.connected:
            raise MT5ConnectionError(
                "MT5 is not connected."
            )

        info = mt5.account_info()

        if info is None:
            raise MT5ConnectionError(
                "Unable to retrieve account information."
            )

        return info

    # =====================================================
    # Health
    # =====================================================

    def health_check(self) -> bool:
        """
        Verify MT5 connection health.
        """

        try:

            if not self.connected:
                return False

            return mt5.version() is not None

        except Exception:

            return False


connection = MT5Connection()
