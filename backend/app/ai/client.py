"""
Ollama Client.
"""

from __future__ import annotations

import json
import time

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
        """

        last_error: Exception | None = None

        for attempt in range(1, settings.OLLAMA_MAX_RETRIES + 1):

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
                    raise ValueError(
                        "Empty response received from Ollama."
                    )

                return result

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Ollama attempt %d failed: %s",
                    attempt,
                    exc,
                )
                time.sleep(min(attempt * 2, 5))

        logger.exception(
            "Ollama request failed after retries: %s",
            last_error,
        )

        fallback = {
            "signal": "HOLD",
            "confidence": 0,
            "reason": [
                "Ollama is unavailable.",
                str(last_error),
            ],
        }

        return json.dumps(fallback)


ollama_client = OllamaClient()
