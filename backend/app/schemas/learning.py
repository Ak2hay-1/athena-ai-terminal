"""Learning API response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class LearningDashboardResponse(BaseModel):
    sample_size: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    weight_version: str = "baseline"
    learning_version: str = "1.0.0"
    features: list[dict[str, Any]] = Field(default_factory=list)
    symbols: list[dict[str, Any]] = Field(default_factory=list)
    timeframes: list[dict[str, Any]] = Field(default_factory=list)
    regimes: list[dict[str, Any]] = Field(default_factory=list)
    strategies: list[dict[str, Any]] = Field(default_factory=list)
    calibration: list[dict[str, Any]] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)
