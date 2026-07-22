"""
Risk engine domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class EntryType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    NONE = "NONE"


class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(slots=True)
class ZoneLevel:
    """Price zone or level with provenance."""

    price: float
    kind: str
    high: float | None = None
    low: float | None = None
    direction: str | None = None


@dataclass(slots=True)
class StructureContext:
    """Market structure snapshot used by risk services."""

    symbol: str
    timeframe: str
    price: float
    atr: float
    trend: str
    volume: float
    avg_volume: float
    bos_active: bool
    bos_direction: str | None
    choch_active: bool
    choch_direction: str | None
    in_premium: bool
    in_discount: bool
    equilibrium: float | None
    range_high: float | None
    range_low: float | None
    swing_highs: list[float] = field(default_factory=list)
    swing_lows: list[float] = field(default_factory=list)
    bullish_order_blocks: list[ZoneLevel] = field(default_factory=list)
    bearish_order_blocks: list[ZoneLevel] = field(default_factory=list)
    bullish_fvgs: list[ZoneLevel] = field(default_factory=list)
    bearish_fvgs: list[ZoneLevel] = field(default_factory=list)
    equal_highs: list[float] = field(default_factory=list)
    equal_lows: list[float] = field(default_factory=list)
    liquidity_sweep_highs: list[float] = field(default_factory=list)
    liquidity_sweep_lows: list[float] = field(default_factory=list)
    liquidity_targets_high: list[ZoneLevel] = field(default_factory=list)
    liquidity_targets_low: list[ZoneLevel] = field(default_factory=list)
    multi_tf_trend: str | None = None
    news_high_impact: bool = False
    news_sentiment: float | None = None
    atr_ok: bool = True
    tight_range: bool = False


@dataclass(slots=True)
class StopLossResult:
    stop_loss: float
    sl_reason: str
    risk_distance: float
    used_structure: str
    valid: bool = True


@dataclass(slots=True)
class TakeProfitResult:
    take_profit: float
    tp_reason: str
    reward_distance: float
    at_liquidity: bool
    risk_reward: float


@dataclass(slots=True)
class EntryResult:
    entry: float
    entry_type: EntryType
    entry_reason: str


class ValidationFlags(BaseModel):
    model_config = ConfigDict(extra="ignore")

    trend: bool = False
    bos: bool = False
    choch: bool = False
    volume: bool = False
    atr: bool = False
    liquidity: bool = False
    news: bool = False
    structure_sl: bool = False
    risk_distance: bool = False
    risk_reward: bool = False
    spread: bool = True
    mtf: bool = True
    regime: bool = True


class TradePlan(BaseModel):
    """Institutional risk-engine output."""

    model_config = ConfigDict(extra="ignore")

    signal: str = "NO_TRADE"
    entry: float = 0.0
    entry_type: EntryType = EntryType.NONE
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_pips: float = 0.0
    reward_pips: float = 0.0
    risk_reward: float = 0.0
    confidence: int = Field(default=0, ge=0, le=100)
    sl_reason: str = ""
    tp_reason: str = ""
    entry_reason: str = ""
    trend: str = "SIDEWAYS"
    validation: ValidationFlags = Field(default_factory=ValidationFlags)
    reasons: list[str] = Field(default_factory=list)


@dataclass(slots=True)
class RiskPlanBundle:
    """Risk engine output pairing the trade plan with its structure context."""

    plan: TradePlan
    context: StructureContext
