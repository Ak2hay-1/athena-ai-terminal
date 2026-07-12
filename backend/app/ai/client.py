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
    Ollama API Client.
    """

    def __init__(self):

        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL

    def generate(
        self,
        prompt: str,
    ) -> str:

        try:

            response = requests.post(

                f"{self.base_url}/api/generate",

                json={

                    "model": self.model,

                    "prompt": prompt,

                    "stream": False,
                },

                timeout=180,

            )

            response.raise_for_status()

            data = response.json()

            return data["response"]

        except Exception as exc:

            logger.exception(exc)

            return json.dumps(

                {

                    "signal": "WAIT",

                    "confidence": 0,

                    "reason": str(exc),

                }

            )


ollama_client = OllamaClient()