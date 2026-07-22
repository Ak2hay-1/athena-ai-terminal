"""
Institutional recommendation enrichment schemas.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ConfidenceCategoryScore(BaseModel):
    """Score contribution and category maximum for UI bars."""

    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    max: int = Field(ge=0, le=100)


class ConfidenceBreakdown(BaseModel):
    """
    Confidence remapped into institutional categories.

    Category ints sum exactly to the recommendation confidence.
    """

    model_config = ConfigDict(extra="ignore")

    trend: int = Field(default=0, ge=0, le=100)
    momentum: int = Field(default=0, ge=0, le=100)
    structure: int = Field(default=0, ge=0, le=100)
    liquidity: int = Field(default=0, ge=0, le=100)
    news: int = Field(default=0, ge=0, le=100)
    risk: int = Field(default=0, ge=0, le=100)

    # Category maxima (for UI bars); derived from ConfidenceEngine weights.
    trend_max: int = Field(default=35, ge=0, le=100)
    momentum_max: int = Field(default=15, ge=0, le=100)
    structure_max: int = Field(default=20, ge=0, le=100)
    liquidity_max: int = Field(default=15, ge=0, le=100)
    news_max: int = Field(default=10, ge=0, le=100)
    risk_max: int = Field(default=5, ge=0, le=100)


class ChecklistItem(BaseModel):
    """Single institutional checklist gate."""

    model_config = ConfigDict(extra="ignore")

    name: str = ""
    passed: bool = False


class MarketHeatmap(BaseModel):
    """Normalized 0–100 visual market factors (not trading decisions)."""

    model_config = ConfigDict(extra="ignore")

    trend: int = Field(default=0, ge=0, le=100)
    momentum: int = Field(default=0, ge=0, le=100)
    structure: int = Field(default=0, ge=0, le=100)
    liquidity: int = Field(default=0, ge=0, le=100)
    volatility: int = Field(default=0, ge=0, le=100)
    news: int = Field(default=0, ge=0, le=100)
    risk: int = Field(default=0, ge=0, le=100)


class EntryZone(BaseModel):
    """Smart entry zone derived from ATR / OB / FVG / liquidity."""

    model_config = ConfigDict(extra="ignore")

    aggressive: float = 0.0
    optimal_low: float = 0.0
    optimal_high: float = 0.0
    conservative: float = 0.0
