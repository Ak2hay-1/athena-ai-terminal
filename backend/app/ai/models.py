"""
AI Models.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.core.enums import RecommendationSignal


class AIRecommendation(BaseModel):
    """
    Final recommendation produced by Athena.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
    )

    signal: RecommendationSignal = RecommendationSignal.HOLD

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    # Trading levels
    entry: float = 0.0

    stop_loss: float = 0.0

    take_profit: float = 0.0

    risk_reward: float = 0.0

    # AI reasoning
    reason: list[str] = Field(
        default_factory=list,
    )

    # Analysis metadata
    trend: str | None = None

    confluence: int | None = None

    timeframe: str | None = None

    symbol: str | None = None
