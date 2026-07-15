"""
Trading account schemas.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class TradeAccount(BaseModel):
    """
    Unified trading account model.

    Represents the current state of a broker or paper
    trading account.
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        extra="forbid",
    )

    login: int | None = Field(
        default=None,
        description="Broker account number.",
    )

    server: str | None = None

    company: str | None = None

    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
    )

    leverage: int = Field(
        default=1,
        ge=1,
    )

    balance: Decimal = Decimal("0")

    equity: Decimal = Decimal("0")

    margin: Decimal = Decimal("0")

    free_margin: Decimal = Decimal("0")

    margin_level: Decimal | None = None

    profit: Decimal = Decimal("0")

    credit: Decimal = Decimal("0")

    trade_allowed: bool = True

    trade_expert: bool = True