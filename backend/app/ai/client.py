"""
Ollama Client.
"""

from __future__ import annotations

import json

import requests

from app.core.logger import logger
from app.core.settings import settings


class OllamaClient:
    """
    Client for communicating with the local Ollama server.
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Send a prompt to Ollama and return the generated response.

        Always returns a JSON string so the ResponseParser
        receives a predictable payload.
        """

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=settings.OLLAMA_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            result = data.get("response", "")

            if not result:
                raise ValueError("Empty response received from Ollama.")

            return result

        except Exception as exc:
            logger.exception("Ollama request failed: %s", exc)

            # Return a valid AIRecommendation JSON so the
            # parser doesn't crash with ValidationError.
            fallback = {
                "signal": "HOLD",
                "confidence": 0.0,
                "entry": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0,
                "risk_reward": 0.0,
                "reason": [
                    "Ollama is unavailable.",
                    str(exc),
                ],
            }

            return json.dumps(fallback)


ollama_client = OllamaClient()
