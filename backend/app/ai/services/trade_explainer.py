"""Thin trade explanation service."""

from __future__ import annotations

from collections.abc import Iterator

from app.ai.schemas.context import MarketContext
from app.ai.schemas.responses import TradeExplanationResponse
from app.ai.services.ai_service import ai_service


class TradeExplainer:
    def explain(self, context: MarketContext) -> TradeExplanationResponse:
        return ai_service.generate_trade_explanation(context)

    def explain_stream(self, context: MarketContext) -> Iterator[str]:
        return ai_service.explain_trade_stream(context)


trade_explainer = TradeExplainer()
