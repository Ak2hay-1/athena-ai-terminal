"""AI services package.

Import the singleton from the submodule to avoid shadowing:

    from app.ai.services.ai_service import ai_service
"""

from app.ai.services.ai_service import AIService

__all__ = ["AIService"]
