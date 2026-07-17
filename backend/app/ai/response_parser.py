"""
AI Response Parser.

Converts LLM JSON responses into validated structures.
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

    def parse_reasons(
        self,
        response: str,
    ) -> list[str]:
        """
        Extract narrative reasons only; ignore any prices/confidence the model invents.
        """
        try:
            if not response:
                return []
            extracted = self._extract_json(response)
            data, _ = self._loads_json(extracted)
            reasons = data.get("reason") or data.get("reasons") or []
            if isinstance(reasons, str):
                return [reasons]
            if isinstance(reasons, list):
                return [str(item) for item in reasons if str(item).strip()]
        except Exception as exc:
            logger.warning("Failed to parse AI reasons: %s", exc)
        return []

    def parse(
        self,
        response: str,
    ) -> AIRecommendation:

        try:

            if not response:
                raise ValueError("Empty AI response.")

            extracted = self._extract_json(response)
            data, _load_path = self._loads_json(extracted)

            # Strip level fields — risk engine owns them.
            for key in (
                "entry",
                "stop_loss",
                "take_profit",
                "risk_reward",
                "entry_type",
                "risk_pips",
                "reward_pips",
                "sl_reason",
                "tp_reason",
            ):
                data.pop(key, None)

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
            confidence=0,
            reason=[
                "Unable to generate AI recommendation."
            ],
        )

    def _loads_json(self, payload: str) -> tuple[dict, str]:
        """
        Parse model JSON, with light repair for common LLM mistakes.
        """

        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                return data, "strict"
        except json.JSONDecodeError:
            pass

        repaired = re.sub(r",(\s*[}\]])", r"\1", payload)
        try:
            data = json.loads(repaired)
            if isinstance(data, dict):
                return data, "trailing_comma_repair"
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for index, char in enumerate(payload):
            if char != "{":
                continue
            try:
                data, _end = decoder.raw_decode(payload[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data, "raw_decode"

        raise json.JSONDecodeError(
            "Unable to decode AI JSON payload",
            payload,
            0,
        )

    def _extract_json(self, response: str) -> str:
        stripped = response.strip()

        balanced = self._balanced_object(stripped)
        if balanced is not None:
            return balanced

        code_block = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            stripped,
            re.DOTALL,
        )

        if code_block:
            return code_block.group(1)

        return stripped

    def _balanced_object(self, text: str) -> str | None:
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escape = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]

        return None


response_parser = ResponseParser()
