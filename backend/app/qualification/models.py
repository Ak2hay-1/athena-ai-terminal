"""Qualification / institutional desk domain models."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class MarketRegime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    BREAKOUT = "BREAKOUT"
    COMPRESSION = "COMPRESSION"
    EXPANSION = "EXPANSION"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


class SetupQualityGrade(str, Enum):
    ELITE = "Elite"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    WATCHLIST = "Watchlist"
    NO_TRADE = "No Trade"


class SetupLifecycleState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    WAITING_ENTRY = "WAITING_ENTRY"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
    TP = "TP"
    SL = "SL"


class ScannerQualityGroup(str, Enum):
    ELITE = "elite"
    HIGH_QUALITY = "high_quality"
    WATCHLIST = "watchlist"
    NO_TRADE = "no_trade"


@dataclass(slots=True)
class GateCheck:
    """Single qualification / rejection gate with pass/fail."""

    name: str
    passed: bool
    detail: str = ""
    mandatory: bool = True


@dataclass(slots=True)
class QualificationResult:
    """Lightweight pre-risk gate result. No entry/SL/TP/confidence."""

    qualified: bool
    reasons: list[str] = field(default_factory=list)
    quality_score: int = 0
    regime: str = MarketRegime.RANGING.value
    gates: list[GateCheck] = field(default_factory=list)
    trend_strength: float = 0.0
    session: str = ""
    thresholds: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class SetupQualityResult:
    """Setup quality separate from confidence."""

    score: int
    grade: str
    components: dict[str, float] = field(default_factory=dict)
    category: str = ScannerQualityGroup.NO_TRADE.value


@dataclass(slots=True)
class RankedOpportunity:
    """Ranked actionable or watchlist opportunity."""

    symbol: str
    timeframe: str
    signal: str
    setup_quality: int
    confidence: int
    risk_reward: float
    trend_strength: float
    historical_win_rate: int
    rank_score: float
    group: str
    correlated: bool = False
    correlation_note: str = ""
