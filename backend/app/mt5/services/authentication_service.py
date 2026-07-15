"""
MetaTrader 5 Authentication Service.

Handles MT5 account authentication.
"""

from __future__ import annotations

from app.core.logger import get_logger
from app.mt5.interfaces import IMT5Manager

logger = get_logger(__name__)


class AuthenticationService:
    """
    Authentication service.

    Responsibilities
    ----------------
    - Login
    - Logout
    - Authentication state
    """

    def __init__(
        self,
        manager: IMT5Manager,
    ) -> None:
        self._manager = manager

        self._logged_in = False

        self._login: int | None = None

    # =====================================================
    # Authentication
    # =====================================================

    def login(
        self,
        *,
        login: int,
        password: str,
        server: str,
        timeout: int = 60000,
    ) -> bool:
        """
        Login to an MT5 account.
        """

        success = self._manager.login(
            login=login,
            password=password,
            server=server,
            timeout=timeout,
        )

        self._logged_in = success

        self._login = login

        logger.info(
            "Authenticated MT5 account %s",
            login,
        )

        return success

    def logout(self) -> None:
        """
        Clear authentication state.

        MT5 Python does not provide a dedicated logout API.
        The session ends when another login occurs or the
        terminal is shut down.
        """

        logger.info("Clearing MT5 authentication state.")

        self._logged_in = False

        self._login = None

    # =====================================================
    # Properties
    # =====================================================

    @property
    def authenticated(self) -> bool:
        """
        Whether an account is authenticated.
        """

        return self._logged_in

    @property
    def login_id(self) -> int | None:
        """
        Current authenticated account.
        """

        return self._login
