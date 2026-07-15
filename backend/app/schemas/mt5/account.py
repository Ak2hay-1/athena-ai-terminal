"""
MT5 Account Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ==========================================================
# Base
# ==========================================================

class MT5AccountBase(BaseModel):
    """
    Base MT5 account information.
    """

    login: int

    name: str

    server: str

    company: str

    currency: str

    leverage: int

    balance: Decimal = Field(decimal_places=2)

    equity: Decimal = Field(decimal_places=2)

    profit: Decimal = Field(decimal_places=2)

    credit: Decimal = Field(decimal_places=2)

    margin: Decimal = Field(decimal_places=2)

    margin_free: Decimal = Field(decimal_places=2)

    margin_level: Decimal = Field(decimal_places=2)

    assets: Decimal = Field(decimal_places=2)

    liabilities: Decimal = Field(decimal_places=2)

    commission_blocked: Decimal = Field(decimal_places=2)


# ==========================================================
# Read
# ==========================================================

class MT5AccountInfo(MT5AccountBase):
    """
    MT5 account information.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    trade_allowed: bool

    trade_expert: bool

    margin_mode: int

    fifo_close: bool

    limit_orders: int

    currency_digits: int

    user_id: int | None = None

    connected: bool = True

    timestamp: datetime


# ==========================================================
# Connection Status
# ==========================================================

class MT5ConnectionStatus(BaseModel):
    """
    MT5 connection status.
    """

    connected: bool

    initialized: bool

    logged_in: bool

    server: str | None = None

    login: int | None = None

    message: str


# ==========================================================
# Login Request
# ==========================================================

class MT5LoginRequest(BaseModel):
    """
    MT5 login request.
    """

    login: int

    password: str = Field(
        min_length=1,
    )

    server: str

    timeout: int = Field(
        default=60000,
        ge=1000,
        le=300000,
    )


# ==========================================================
# Login Response
# ==========================================================

class MT5LoginResponse(BaseModel):
    """
    Login response.
    """

    success: bool

    message: str

    account: MT5AccountInfo | None = None


# ==========================================================
# Logout Response
# ==========================================================

class MT5LogoutResponse(BaseModel):
    """
    Logout response.
    """

    success: bool

    message: str


# ==========================================================
# Account Summary
# ==========================================================

class MT5AccountSummary(BaseModel):
    """
    Lightweight account summary.
    """

    login: int

    server: str

    balance: Decimal

    equity: Decimal

    profit: Decimal

    margin_free: Decimal

    currency: str