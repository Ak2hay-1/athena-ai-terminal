"""Abstract AI provider interface."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

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
