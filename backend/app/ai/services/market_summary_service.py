"""Thin market summary service."""

from __future__ import annotations

from app.ai.schemas.context import MarketContext
from app.ai.schemas.responses import MarketSummaryResponse
from app.ai.services.ai_service import ai_service


class MarketSummaryService:
    def summarize(self, context: MarketContext) -> MarketSummaryResponse:
        return ai_service.generate_market_summary(context)


market_summary_service = MarketSummaryService()
