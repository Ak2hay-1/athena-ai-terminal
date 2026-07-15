"""
MT5 Terminal Schemas.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Terminal Information
# ==========================================================

class MT5TerminalInfo(BaseModel):
    """
    MetaTrader 5 terminal information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    company: str

    name: str

    language: str

    path: str

    data_path: str

    commondata_path: str

    community_account: bool

    community_connection: bool

    connected: bool

    trade_allowed: bool

    tradeapi_disabled: bool

    dlls_allowed: bool

    email_enabled: bool

    ftp_enabled: bool

    notifications_enabled: bool

    mqid: bool

    build: int

    maxbars: int

    ping_last: int

    codepage: int


# ==========================================================
# Version Information
# ==========================================================

class MT5VersionInfo(BaseModel):
    """
    MT5 version information.
    """

    version: int

    build: int

    release_date: str

    description: str | None = None


# ==========================================================
# Terminal Status
# ==========================================================

class MT5TerminalStatus(BaseModel):
    """
    Current MT5 terminal status.
    """

    initialized: bool

    connected: bool

    logged_in: bool

    trading_enabled: bool

    expert_enabled: bool

    dll_enabled: bool

    server: str | None = None

    login: int | None = None

    message: str

    timestamp: datetime


# ==========================================================
# Terminal Health
# ==========================================================

class MT5TerminalHealth(BaseModel):
    """
    Terminal health information.
    """

    status: str = Field(
        description="healthy, warning or error",
    )

    initialized: bool

    connected: bool

    ping_ms: int

    uptime_seconds: int

    last_check: datetime

    message: str


# ==========================================================
# Initialize Request
# ==========================================================

class MT5InitializeRequest(BaseModel):
    """
    Initialize MT5 terminal.
    """

    terminal_path: str | None = None

    portable: bool = False

    timeout: int = Field(
        default=60000,
        ge=1000,
        le=300000,
    )


# ==========================================================
# Initialize Response
# ==========================================================

class MT5InitializeResponse(BaseModel):
    """
    Initialize response.
    """

    success: bool

    message: str

    terminal: MT5TerminalInfo | None = None


# ==========================================================
# Shutdown Response
# ==========================================================

class MT5ShutdownResponse(BaseModel):
    """
    Shutdown response.
    """

    success: bool

    message: str

    timestamp: datetime