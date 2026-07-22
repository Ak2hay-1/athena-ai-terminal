"""Abstract AI provider interface."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from app.ai.schemas.context import ChatMessage
from app.ai.schemas.responses import ProviderTextResult


class AIProvider(ABC):
    """
    Transport-level provider contract.

    High-level tasks (trade explanation, summaries) live on AIService.
    """

    name: str

    @abstractmethod
    def generate_text(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
    ) -> ProviderTextResult:
        raise NotImplementedError

    @abstractmethod
    def chat(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> ProviderTextResult:
        raise NotImplementedError

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    def models(self) -> list[str]:
        """Return available model tags when supported."""
        return [self.model_name()]

    def generate_text_stream(
        self,
        *,
        system: str,
        user: str,
        json_mode: bool = False,
    ) -> Iterator[str]:
        """
        Yield text deltas. Default falls back to a single full response.
        """
        result = self.generate_text(system=system, user=user, json_mode=json_mode)
        if result.text:
            yield result.text

    def chat_stream(
        self,
        *,
        messages: list[ChatMessage],
        system: str | None = None,
    ) -> Iterator[str]:
        """
        Yield chat token deltas. Default falls back to a single full response.
        """
        result = self.chat(messages=messages, system=system)
        if result.text:
            yield result.text
