"""
Athena Domain Enums.

Shared enums used across the application.
"""

from __future__ import annotations

from enum import Enum


class RecommendationSignal(str, Enum):
    """Trading recommendation."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"


class TrendDirection(str, Enum):
    """Market trend direction."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"


class RiskLevel(str, Enum):
    """Recommendation risk."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
