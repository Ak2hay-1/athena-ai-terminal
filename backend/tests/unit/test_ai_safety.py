"""Safety layer tests for Local AI communication."""

from __future__ import annotations

from app.ai.safety import REDIRECT_MESSAGE
from app.ai.safety import detect_decision_request
from app.ai.safety import filter_response
from app.ai.safety import last_user_message
from app.ai.schemas.context import ChatMessage


def test_detects_should_i_buy():
    result = detect_decision_request("Should I BUY gold now?")
    assert result.blocked is True
    assert result.redirect_message == REDIRECT_MESSAGE


def test_allows_explain_questions():
    result = detect_decision_request("Explain why Athena chose this stop loss.")
    assert result.blocked is False


def test_last_user_message():
    messages = [
        ChatMessage(role="assistant", content="hi"),
        ChatMessage(role="user", content="Should I sell?"),
    ]
    assert "sell" in last_user_message(messages).lower()


def test_filter_response_appends_note_on_advice():
    text = "I recommend you buy XAUUSD at the next pullback."
    filtered = filter_response(text)
    assert "frozen recommendation remains authoritative" in filtered.lower()
