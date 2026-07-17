"""
AI package exports.

Business logic should use ai_service only.
"""

from app.ai.models import AIRecommendation
from app.ai.services.ai_service import ai_service

__all__ = [
    "ai_service",
    "AIRecommendation",
]
