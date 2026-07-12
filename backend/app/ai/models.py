"""
AI Response Models.
"""

from pydantic import BaseModel
from pydantic import Field


class AIRecommendation(BaseModel):

    signal: str = Field(...)

    confidence: float = Field(...)

    entry: float

    stop_loss: float

    take_profit: float

    risk_reward: float

    reason: list[str]