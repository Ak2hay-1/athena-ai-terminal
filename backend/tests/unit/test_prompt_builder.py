"""PromptBuilder sanitization tests."""

from __future__ import annotations

from app.ai.prompts import chat as chat_prompt
from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import TradeCandidate


def test_prompt_builder_strips_ohlc_candles():
    payload = PromptBuilder.from_analysis_dict(
        {
            "symbol": "XAUUSD",
            "candles": [
                {"open": 1, "high": 2, "low": 0.5, "close": 1.5},
            ],
            "trend": "Bullish",
            "indicator_history": [1, 2, 3],
        }
    )
    assert "candles" not in payload
    assert "indicator_history" not in payload
    assert payload["trend"] == "Bullish"


def test_chat_system_prompt_includes_athena_finalized_rule():
    system = chat_prompt.build_system()
    assert "ALREADY finalize" in system or "ALREADY" in system
    assert "never invent" in system.lower() or "You never invent" in system


def test_chat_system_with_context_uses_safe_trade_plan():
    context = MarketContext(
        symbol="XAUUSD",
        timeframe="M5",
        trend="Bullish",
        trade_candidate=TradeCandidate(signal="BUY", confidence=70),
    )
    system = chat_prompt.build_system(context)
    assert "XAUUSD" in system
    assert "candles" not in system.lower()
