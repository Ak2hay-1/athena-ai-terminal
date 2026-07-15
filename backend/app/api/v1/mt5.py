"""
MetaTrader 5 API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from app.auth.dependencies import require_admin
from app.models.user import User
from app.schemas.mt5 import (
    MT5AccountInfo,
    MT5ConnectionStatus,
    MT5LoginRequest,
    MT5LoginResponse,
    MT5LogoutResponse,
    MT5TerminalInfo,
    MT5VersionInfo,
)
from app.services.mt5_service import MT5Service, mt5_service

router = APIRouter(
    prefix="/mt5",
    tags=["MetaTrader 5"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_mt5_service() -> MT5Service:
    """
    MT5 service dependency.
    """

    return mt5_service


# ==========================================================
# Initialize
# ==========================================================

@router.post(
    "/initialize",
    response_model=bool,
    summary="Initialize MT5 Terminal",
)
def initialize_terminal(
    path: str | None = None,
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> bool:
    """
    Initialize the MT5 terminal.
    """

    return service.initialize(path)


# ==========================================================
# Login
# ==========================================================

@router.post(
    "/login",
    response_model=MT5LoginResponse,
    summary="Login to MT5",
)
def login(
    request: MT5LoginRequest,
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5LoginResponse:
    """
    Login to an MT5 trading account.
    """

    return service.login(request)


# ==========================================================
# Shutdown
# ==========================================================

@router.post(
    "/shutdown",
    response_model=MT5LogoutResponse,
    summary="Shutdown MT5",
)
def shutdown(
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5LogoutResponse:
    """
    Shutdown the MT5 terminal.
    """

    return service.shutdown()


# ==========================================================
# Status
# ==========================================================

@router.get(
    "/status",
    response_model=MT5ConnectionStatus,
    summary="MT5 Connection Status",
)
def status(
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5ConnectionStatus:
    """
    Retrieve MT5 connection status.
    """

    return service.status()


# ==========================================================
# Account
# ==========================================================

@router.get(
    "/account",
    response_model=MT5AccountInfo,
    summary="Account Information",
)
def account(
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5AccountInfo:
    """
    Retrieve trading account information.
    """

    return service.get_account_info()


# ==========================================================
# Terminal
# ==========================================================

@router.get(
    "/terminal",
    response_model=MT5TerminalInfo,
    summary="Terminal Information",
)
def terminal(
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5TerminalInfo:
    """
    Retrieve terminal information.
    """

    return service.get_terminal_info()


# ==========================================================
# Version
# ==========================================================

@router.get(
    "/version",
    response_model=MT5VersionInfo,
    summary="MT5 Version",
)
def version(
    _: User = Depends(require_admin),
    service: MT5Service = Depends(get_mt5_service),
) -> MT5VersionInfo:
    """
    Retrieve MT5 version information.
    """

    return service.get_version()