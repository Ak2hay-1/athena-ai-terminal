"""
Agent event type definitions.
"""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """Canonical event types for the agent orchestrator."""

    MARKET_UPDATED = "MarketUpdated"
    TRADE_CREATED = "TradeCreated"
    TRADE_CLOSED = "TradeClosed"
    NEWS_RECEIVED = "NewsReceived"
    RISK_CHANGED = "RiskChanged"
    RECOMMENDATION_GENERATED = "RecommendationGenerated"
    RECOMMENDATION_VALIDATED = "RecommendationValidated"
    SYSTEM_TICK = "SystemTick"
    TECHNICAL_ANALYSIS_COMPLETED = "TechnicalAnalysisCompleted"
    SMC_ANALYSIS_COMPLETED = "SMCAnalysisCompleted"
    RISK_ASSESSMENT_COMPLETED = "RiskAssessmentCompleted"
    TRADE_VALIDATION_COMPLETED = "TradeValidationCompleted"
    LEARNING_COMPLETED = "LearningCompleted"
    NEWS_ANALYSIS_COMPLETED = "NewsAnalysisCompleted"
    REASONING_COMPLETED = "ReasoningCompleted"
    PORTFOLIO_UPDATED = "PortfolioUpdated"
    WATCHLIST_OPPORTUNITY_DETECTED = "WatchlistOpportunityDetected"
    NOTIFICATION_DISPATCHED = "NotificationDispatched"
