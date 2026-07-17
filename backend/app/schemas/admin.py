"""
Admin panel schemas.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class AdminHealthSummary(BaseModel):
    status: str
    database: str
    service: str
    version: str


class AdminMt5Summary(BaseModel):
    connected: bool
    initialized: bool
    logged_in: bool
    server: str | None = None
    login: int | None = None
    message: str


class AdminLearningSummary(BaseModel):
    enabled: bool
    min_samples: int
    retrain_interval_hours: int
    model_path: str


class AdminUsersSummary(BaseModel):
    total: int
    active: int
    admins: int


class AdminConfigSummary(BaseModel):
    app_env: str
    execution_provider: str
    market_symbols: list[str] = Field(default_factory=list)
    market_timeframes: list[str] = Field(default_factory=list)
    ai_provider: str
    ai_model: str
    ollama_model: str | None = None
    collector_interval_seconds: int


class AdminOverview(BaseModel):
    health: AdminHealthSummary
    mt5: AdminMt5Summary
    learning: AdminLearningSummary
    users: AdminUsersSummary
    config: AdminConfigSummary


class SchedulerJobStatus(BaseModel):
    id: str
    name: str
    next_run_time: str | None = None
    trigger: str


class SchedulerStatus(BaseModel):
    name: str
    running: bool
    jobs: list[SchedulerJobStatus] = Field(default_factory=list)


class AdminSchedulersResponse(BaseModel):
    market: SchedulerStatus
    news_learning: SchedulerStatus
    timezone: str


class SchedulerTriggerResponse(BaseModel):
    triggered: str
    next_run_time: str
    timeframe: str | None = None


class NewsSyncResponse(BaseModel):
    inserted: int


class MarketCleanupResponse(BaseModel):
    deleted: int
    before: str
