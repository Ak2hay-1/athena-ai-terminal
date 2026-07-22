"""LocalProvider (Ollama) unit tests with mocked HTTP."""

from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import patch

from app.ai.providers.local_provider import LocalProvider
from app.ai.schemas.context import ChatMessage


def _provider(monkeypatch) -> LocalProvider:
    monkeypatch.setattr(
        "app.ai.providers.local_provider.settings",
        type(
            "S",
            (),
            {
                "OLLAMA_HOST": "http://127.0.0.1:11434",
                "OLLAMA_MODEL": "llama3.2",
                "OLLAMA_EMBED_MODEL": "nomic-embed-text",
                "OLLAMA_TIMEOUT": 30,
                "OLLAMA_TEMPERATURE": 0.3,
                "OLLAMA_TOP_P": 0.9,
                "OLLAMA_MAX_TOKENS": 256,
            },
        )(),
    )
    return LocalProvider()


def test_health_and_models(monkeypatch):
    provider = _provider(monkeypatch)
    tags = {
        "models": [
            {"name": "llama3.2:latest"},
            {"name": "mistral:latest"},
        ]
    }

    with patch("app.ai.providers.local_provider.requests.get") as get:
        response = MagicMock()
        response.ok = True
        response.json.return_value = tags
        get.return_value = response

        assert provider.health() is True
        assert provider.models() == ["llama3.2:latest", "mistral:latest"]


def test_generate_text(monkeypatch):
    provider = _provider(monkeypatch)

    with patch("app.ai.providers.local_provider.requests.post") as post:
        response = MagicMock()
        response.ok = True
        response.json.return_value = {
            "response": "hello from ollama",
            "prompt_eval_count": 5,
            "eval_count": 3,
        }
        post.return_value = response

        result = provider.generate_text(system="sys", user="user")
        assert result.text == "hello from ollama"
        assert result.provider == "local"
        payload = post.call_args.kwargs["json"]
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.3


def test_generate_text_stream_assembles_chunks(monkeypatch):
    provider = _provider(monkeypatch)

    lines = [
        json.dumps({"response": "Hel", "done": False}),
        json.dumps({"response": "lo", "done": False}),
        json.dumps({"response": "", "done": True}),
    ]

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.iter_lines.return_value = lines
    mock_response.__enter__ = lambda self: mock_response
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("app.ai.providers.local_provider.requests.post", return_value=mock_response):
        chunks = list(
            provider.generate_text_stream(system="sys", user="user")
        )

    assert chunks == ["Hel", "lo"]
    assert "".join(chunks) == "Hello"


def test_chat_stream_assembles_chunks(monkeypatch):
    provider = _provider(monkeypatch)
    lines = [
        json.dumps({"message": {"content": "A"}, "done": False}),
        json.dumps({"message": {"content": "B"}, "done": True}),
    ]
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.iter_lines.return_value = lines
    mock_response.__enter__ = lambda self: mock_response
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("app.ai.providers.local_provider.requests.post", return_value=mock_response):
        chunks = list(
            provider.chat_stream(
                messages=[ChatMessage(role="user", content="hi")],
                system="sys",
            )
        )

    assert "".join(chunks) == "AB"
