"""Thin chat service with safety rails via AIService."""

from __future__ import annotations

from collections.abc import Iterator

from app.ai.schemas.context import ChatMessage
from app.ai.schemas.context import MarketContext
from app.ai.schemas.responses import ChatResponse
from app.ai.services.ai_service import ai_service


class ChatService:
    def chat(
        self,
        messages: list[ChatMessage],
        context: MarketContext | None = None,
    ) -> ChatResponse:
        return ai_service.chat(messages, context=context)

    def chat_stream(
        self,
        messages: list[ChatMessage],
        context: MarketContext | None = None,
    ) -> Iterator[str]:
        return ai_service.chat_stream(messages, context=context)


chat_service = ChatService()
