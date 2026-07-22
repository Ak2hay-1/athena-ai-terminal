"""
Scanner opportunity schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ScannerScoreBreakdown(BaseModel):
    """Explainable components of the scanner rank score (0–100 scale inputs)."""

    base: float = 0.0
    quality: float = 0.0
    probability: float = 0.0
    confluence: float = 0.0
    momentum_align: float = 0.0
    freshness: float = 0.0
    session: float = 0.0
    market_watch: float = 0.0
    penalties: float = 0.0


class ScannerOpportunityRead(BaseModel):
    """Single ranked scanner row."""

    id: str
    symbol: str
    timeframe: str
    signal: str
    score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    score_breakdown: ScannerScoreBreakdown
    price: float | None = None
    change_percent: float | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    risk_reward: float | None = None
    trend: str | None = None
    confluence: int | None = None
    trade_quality: int | None = None
    trade_probability: int | None = None
    setup_quality: int | None = None
    setup_quality_grade: str | None = None
    scanner_group: str = "no_trade"
    rejection_checklist: list[dict[str, Any]] = Field(default_factory=list)
    lifecycle_state: str | None = None
    correlated: bool = False
    correlation_note: str = ""
    session: str
    reasons: list[str] = Field(default_factory=list)
    market_watch_tag: str | None = None
    also_hot_on: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    staleness_ms: int | None = None
    stale: bool = False
    recommendation_id: int | None = None


class ScannerGroupCounts(BaseModel):
    """Scanner quality group tallies."""

    elite: int = 0
    high_quality: int = 0
    watchlist: int = 0
    no_trade: int = 0


class ScannerMeta(BaseModel):
    """Freshness / universe metadata for the scanner board."""

    timeframe: str
    universe_size: int
    opportunity_count: int
    generated_at: datetime
    last_market_watch_scan_at: datetime | None = None
    last_market_watch_scan_age_ms: int | None = None
    stale_threshold_minutes: int
    symbols_scanned: list[str] = Field(default_factory=list)
    group_counts: ScannerGroupCounts = Field(default_factory=ScannerGroupCounts)


class ScannerOpportunitiesResponse(BaseModel):
    """Batch scanner response."""

    opportunities: list[ScannerOpportunityRead]
    groups: dict[str, list[ScannerOpportunityRead]] = Field(default_factory=dict)
    meta: ScannerMeta


class ScannerUpdatePayload(BaseModel):
    """WebSocket scanner_update delta (partial fields allowed)."""

    type: str = "scanner_update"
    symbol: str
    timeframe: str | None = None
    opportunity: dict[str, Any] | None = None
    change_type: str | None = None
    price: float | None = None
