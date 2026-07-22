"""Thin strategy teacher service."""

from __future__ import annotations

from app.ai.schemas.responses import StrategyLessonResponse
from app.ai.services.ai_service import ai_service


class StrategyTeacher:
    def teach(self, topic: str) -> StrategyLessonResponse:
        return ai_service.teach_strategy(topic)


strategy_teacher = StrategyTeacher()
