"""Thin indicator education service."""

from __future__ import annotations

from app.ai.schemas.context import MarketContext
from app.ai.schemas.responses import IndicatorExplanationResponse
from app.ai.services.ai_service import ai_service


class IndicatorExplainer:
    def explain(
        self,
        topic: str,
        context: MarketContext | None = None,
    ) -> IndicatorExplanationResponse:
        return ai_service.explain_indicator(topic, context)


indicator_explainer = IndicatorExplainer()
