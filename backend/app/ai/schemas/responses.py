"""Typed AI service response objects."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class ProviderTextResult(BaseModel):
    """Normalized transport result from any AI provider."""

    text: str
    model: str
    provider: str
    latency_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class TradeExplanationResponse(BaseModel):
    reasons: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class MarketSummaryResponse(BaseModel):
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)
    bias: str | None = None
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class NewsSummaryResponse(BaseModel):
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)
    overall_sentiment: str | None = None
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class ChatResponse(BaseModel):
    reply: str = ""
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class EmbeddingsResponse(BaseModel):
    embeddings: list[list[float]] = Field(default_factory=list)
    dimensions: int = 0
    provider: str | None = None
    model: str | None = None
    success: bool = True
    message: str | None = None


# Canonical short aliases used by provider contracts
TradeExplanation = TradeExplanationResponse
MarketSummary = MarketSummaryResponse
NewsSummary = NewsSummaryResponse
