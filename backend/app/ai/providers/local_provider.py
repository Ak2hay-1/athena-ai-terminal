"""Local Ollama AI provider."""

from __future__ import annotations

import time

import requests

from app.ai.providers.base import AIProvider
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.responses import ProviderTextResult
from app.core.settings import settings


class LocalProvider(AIProvider):
    """Ollama HTTP provider (generate / chat / embeddings)."""

    name = "local"

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.embed_model = settings.OLLAMA_EMBED_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    def model_name(self) -> str:
        return self.model

    def health(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=min(5, self.timeout),
            )
            return response.ok
        except Exception:
            return False

    def generate_text(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
    ) -> ProviderTextResult:
        prompt = f"{system.strip()}\n\n{user.strip()}"
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        started = time.perf_counter()
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            detail = response.text.strip() or response.reason
            raise RuntimeError(
                f"Ollama generate failed ({response.status_code}): {detail}"
            )

        data = response.json()
        text = data.get("response") or ""
        if not text:
            raise ValueError("Empty response received from Ollama.")

        latency_ms = (time.perf_counter() - started) * 1000
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )

    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        ollama_messages: list[dict[str, str]] = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        for message in messages:
            ollama_messages.append(
                {"role": message.role, "content": message.content}
            )

        started = time.perf_counter()
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
            },
            timeout=self.timeout,
        )
        if not response.ok:
            detail = response.text.strip() or response.reason
            raise RuntimeError(
                f"Ollama chat failed ({response.status_code}): {detail}"
            )

        data = response.json()
        message = data.get("message") or {}
        text = message.get("content") or ""
        if not text:
            raise ValueError("Empty chat response received from Ollama.")

        latency_ms = (time.perf_counter() - started) * 1000
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text,
                },
                timeout=self.timeout,
            )
            if not response.ok:
                detail = response.text.strip() or response.reason
                raise RuntimeError(
                    f"Ollama embeddings failed ({response.status_code}): {detail}"
                )
            data = response.json()
            embedding = data.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError("Invalid embedding payload from Ollama.")
            vectors.append([float(value) for value in embedding])
        return vectors
