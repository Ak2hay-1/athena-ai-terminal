"""API request/response DTOs for AI endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class ChatMessageIn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: list[ChatMessageIn] = Field(..., min_length=1, max_length=40)
    symbol: str | None = None
    timeframe: str | None = None


class MarketSummaryRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str = "M5"


class NewsSummaryRequest(BaseModel):
    symbol: str = "XAUUSD"
    limit: int = Field(default=20, ge=1, le=50)


class EmbeddingsRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=32)


class ExplainTradeRequest(BaseModel):
    recommendation_id: int | None = None
    symbol: str | None = None
    timeframe: str | None = None
    snapshot: dict[str, Any] | None = None


class ExplainIndicatorRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=64)
    symbol: str | None = None
    timeframe: str | None = None


class TeachRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=64)


class SessionSummaryRequest(BaseModel):
    mode: str | None = "live"
    symbol: str | None = None
    timeframe: str | None = None
    total_recommendations: int | None = None
    signals: dict[str, int] | None = None
    avg_confidence: float | None = None
    win_rate: float | None = None
    started_at: str | None = None
    ended_at: str | None = None
    notes: str | None = None
    recommendations: list[dict[str, Any]] | None = None


class AIEndpointResponse(BaseModel):
    success: bool
    data: dict | list | None = None
    message: str | None = None
