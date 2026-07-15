"""
Recommendation Schemas.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.core.enums import RecommendationSignal
from app.core.enums import TrendDirection


# ==========================================================
# Base
# ==========================================================

class RecommendationBase(BaseModel):
    """
    Base recommendation schema.
    """

    symbol: str = Field(
        min_length=1,
        max_length=20,
    )

    timeframe: str = Field(
        min_length=1,
        max_length=10,
    )

    signal: RecommendationSignal

    confidence: int = Field(
        ge=0,
        le=100,
    )

    trend: TrendDirection

    confluence: int = Field(
        ge=0,
        le=100,
    )

    entry_price: Decimal

    stop_loss: Decimal

    take_profit: Decimal

    risk_reward: Decimal

    analysis: dict[str, Any]

    reasoning: list[str]


# ==========================================================
# Create
# ==========================================================

class RecommendationCreate(RecommendationBase):
    """
    Create recommendation.
    """

    pass


# ==========================================================
# Read
# ==========================================================

class RecommendationRead(RecommendationBase):
    """
    Recommendation response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Query
# ==========================================================

class RecommendationQuery(BaseModel):
    """
    Recommendation query.
    """

    symbol: str

    timeframe: str

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
    )
