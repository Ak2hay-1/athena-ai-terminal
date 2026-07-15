"""
AI Response Parser.

Converts Ollama responses into validated AIRecommendation objects.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.ai.models import AIRecommendation
from app.core.logger import logger


class ResponseParser:
    """
    Parse and validate AI responses.
    """

    def parse(
        self,
        response: str,
    ) -> AIRecommendation:

        try:

            if not response:
                raise ValueError("Empty AI response.")

            data = json.loads(response)

            return AIRecommendation.model_validate(data)

        except json.JSONDecodeError as exc:

            logger.exception(
                "Invalid JSON returned by AI: %s",
                exc,
            )

        except ValidationError as exc:

            logger.exception(
                "AI response validation failed: %s",
                exc,
            )

        except Exception as exc:

            logger.exception(
                "Unexpected AI parser error: %s",
                exc,
            )

        # --------------------------------------------------
        # Safe fallback
        # --------------------------------------------------

        return AIRecommendation(
            signal="HOLD",
            confidence=0.0,
            entry=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            risk_reward=0.0,
            reason=[
                "Unable to generate AI recommendation."
            ],
        )


response_parser = ResponseParser()
