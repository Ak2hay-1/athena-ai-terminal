"""
AI Response Parser.

Responsible for:

- Parsing Ollama responses
- Validating JSON
- Returning AIRecommendation
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

            data = json.loads(response)

            recommendation = AIRecommendation.model_validate(
                data
            )

            return recommendation

        except json.JSONDecodeError as exc:

            logger.exception(exc)

            raise ValueError(
                "AI returned invalid JSON."
            ) from exc

        except ValidationError as exc:

            logger.exception(exc)

            raise ValueError(
                "AI response validation failed."
            ) from exc


response_parser = ResponseParser()