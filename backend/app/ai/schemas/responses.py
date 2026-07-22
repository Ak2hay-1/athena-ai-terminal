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


class ExplanationSections(BaseModel):
    trend: str = ""
    momentum: str = ""
    structure: str = ""
    liquidity: str = ""
    risk: str = ""
    entry_sl_tp: str = ""
    confidence: str = ""
    probability: str = ""
    quality: str = ""


class TradeExplanationResponse(BaseModel):
    reasons: list[str] = Field(default_factory=list)
    sections: ExplanationSections | None = None
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class MarketSummarySections(BaseModel):
    trend: str = ""
    structure: str = ""
    momentum: str = ""
    liquidity: str = ""
    risk: str = ""


class MarketSummaryResponse(BaseModel):
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)
    bias: str | None = None
    sections: MarketSummarySections | None = None
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
    redirected: bool = False


class EmbeddingsResponse(BaseModel):
    embeddings: list[list[float]] = Field(default_factory=list)
    dimensions: int = 0
    provider: str | None = None
    model: str | None = None
    success: bool = True
    message: str | None = None


class IndicatorExplanationResponse(BaseModel):
    topic: str = ""
    summary: str = ""
    how_it_works: list[str] = Field(default_factory=list)
    athena_usage: str = ""
    pitfalls: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class StrategyLessonResponse(BaseModel):
    topic: str = ""
    title: str = ""
    lesson: str = ""
    key_points: list[str] = Field(default_factory=list)
    exercise: str = ""
    common_mistakes: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class SessionSummaryResponse(BaseModel):
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None


class AIHealthResponse(BaseModel):
    healthy: bool
    provider: str
    model: str
    models: list[str] = Field(default_factory=list)
    message: str | None = None


class SetupReasoningResponse(BaseModel):
    summary: str = ""
    institutional_reasoning: str = ""
    potential_risks: list[str] = Field(default_factory=list)
    alternative_scenarios: list[str] = Field(default_factory=list)
    confidence_explanation: str = ""
    what_to_watch: list[str] = Field(default_factory=list)
    evidence_citations: list[str] = Field(default_factory=list)
    similar_trades: dict | None = None
    provider: str | None = None
    model: str | None = None
    cached: bool = False
    success: bool = True
    message: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None


# Canonical short aliases used by provider contracts
TradeExplanation = TradeExplanationResponse
MarketSummary = MarketSummaryResponse
NewsSummary = NewsSummaryResponse
