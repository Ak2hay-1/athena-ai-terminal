"""Anthropic Claude AI provider."""

from __future__ import annotations

import time

from app.ai.providers.base import AIProvider
from app.ai.schemas.context import ChatMessage
from app.ai.schemas.responses import ProviderTextResult
from app.core.settings import settings


class ClaudeProvider(AIProvider):
    """Claude via Anthropic SDK."""

    name = "claude"

    def __init__(self) -> None:
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.timeout = settings.AI_TIMEOUT
        self._client = None

    def model_name(self) -> str:
        return self.model

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
            import anthropic

            self._client = anthropic.Anthropic(
                api_key=self.api_key,
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
        system_text = system
        if json_mode:
            system_text = (
                f"{system.strip()}\n\nRespond with valid JSON only. No markdown."
            )

        started = time.perf_counter()
        response = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_text,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            raise ValueError("Empty response received from Claude.")

        usage = response.usage
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=getattr(usage, "input_tokens", None) if usage else None,
            completion_tokens=(
                getattr(usage, "output_tokens", None) if usage else None
            ),
        )

    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        client = self._get_client()
        payload = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]
        if not payload:
            raise ValueError("Claude chat requires at least one user/assistant message.")

        started = time.perf_counter()
        response = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system or "You are Athena AI, an institutional trading assistant.",
            messages=payload,
        )
        text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            raise ValueError("Empty chat response received from Claude.")

        usage = response.usage
        return ProviderTextResult(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_tokens=getattr(usage, "input_tokens", None) if usage else None,
            completion_tokens=(
                getattr(usage, "output_tokens", None) if usage else None
            ),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError(
            "Claude provider does not support embeddings. "
            "Use OpenAI or Local for generate_embeddings()."
        )
