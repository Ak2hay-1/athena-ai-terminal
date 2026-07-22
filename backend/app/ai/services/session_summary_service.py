"""Thin session summary service."""

from __future__ import annotations

from typing import Any

from app.ai.schemas.responses import SessionSummaryResponse
from app.ai.services.ai_service import ai_service


class SessionSummaryService:
    def summarize(self, stats: dict[str, Any]) -> SessionSummaryResponse:
        return ai_service.summarize_session(stats)


session_summary_service = SessionSummaryService()
