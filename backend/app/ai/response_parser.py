"""
AI Response Parser.

Converts Ollama responses into validated AIRecommendation objects.
"""

from __future__ import annotations

import json
import re

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

            data = json.loads(
                self._extract_json(response)
            )

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

        return AIRecommendation(
            signal="HOLD",
            confidence=0.0,
            reason=[
                "Unable to generate AI recommendation."
            ],
        )

    def _extract_json(self, response: str) -> str:
        stripped = response.strip()

        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped

        code_block = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            stripped,
            re.DOTALL,
        )

        if code_block:
            return code_block.group(1)

        brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)

        if brace_match:
            return brace_match.group(0)

        return stripped


response_parser = ResponseParser()
