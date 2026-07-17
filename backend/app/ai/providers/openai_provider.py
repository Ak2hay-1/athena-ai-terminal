"""OpenAI-compatible AI provider (OpenAI, DeepSeek, Grok)."""

from __future__ import annotations

import time

from app.ai.providers.base import AIProvider
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.responses import ProviderTextResult
from app.core.settings import settings

_PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "embed_model": "text-embedding-3-small",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "embed_model": "text-embedding-3-small",
    },
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "model": "grok-2",
        "embed_model": "text-embedding-3-small",
    },
}


class OpenAIProvider(AIProvider):
    """OpenAI SDK provider; also serves DeepSeek/Grok via base_url."""

    def __init__(self, provider_name: str = "openai") -> None:
        defaults = _PROVIDER_DEFAULTS.get(provider_name, _PROVIDER_DEFAULTS["openai"])
        self.name = provider_name
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.AI_BASE_URL.strip() or defaults["base_url"]
        if provider_name == "openai":
            self.model = settings.OPENAI_MODEL or defaults["model"]
        elif settings.AI_PROVIDER.strip().lower() == provider_name and settings.OPENAI_MODEL:
            self.model = settings.OPENAI_MODEL
        else:
            self.model = defaults["model"]
        self.embed_model = defaults["embed_model"]
        self.timeout = settings.AI_TIMEOUT
        self._client = None

    def model_name(self) -> str:
        return self.model

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured.")
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def health(self) -> bool:
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def generate_text(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
    ) -> ProviderTextResult:
        client = self._get_client()
        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message
        text = (choice.content or "").strip()
        if not text:
            raise ValueError(f"Empty response received from {self.name}.")

        usage = response.usage
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=(
                getattr(usage, "completion_tokens", None) if usage else None
            ),
        )

    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        client = self._get_client()
        payload: list[dict[str, str]] = []
        if system:
            payload.append({"role": "system", "content": system})
        for message in messages:
            payload.append({"role": message.role, "content": message.content})

        started = time.perf_counter()
        response = client.chat.completions.create(
            model=self.model,
            messages=payload,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ValueError(f"Empty chat response received from {self.name}.")

        usage = response.usage
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=(
                getattr(usage, "completion_tokens", None) if usage else None
            ),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        response = client.embeddings.create(
            model=self.embed_model,
            input=texts,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]
