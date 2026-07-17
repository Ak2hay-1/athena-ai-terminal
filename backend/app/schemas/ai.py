"""API request/response DTOs for AI endpoints."""

from __future__ import annotations

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


class AIEndpointResponse(BaseModel):
    success: bool
    data: dict | list | None = None
    message: str | None = None
