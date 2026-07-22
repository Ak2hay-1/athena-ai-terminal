"""Indicator education prompt builder."""

from __future__ import annotations

import json
from enum import Enum

from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.schemas.context import MarketContext


class IndicatorTopic(str, Enum):
    RSI = "rsi"
    MACD = "macd"
    EMA = "ema"
    ATR = "atr"
    VOLUME = "volume"
    FVG = "fvg"
    ORDER_BLOCK = "order_block"
    LIQUIDITY = "liquidity"
    MARKET_STRUCTURE = "market_structure"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    CONFLUENCE = "confluence"


SYSTEM_PROMPT = """
You are Athena AI, an institutional trading educator.

Explain the requested indicator/topic for traders.
Use the frozen Athena market context when provided to show how Athena uses it.
Do NOT invent a trade signal, entry, SL/TP, confidence, or probability.
Do NOT tell the user to buy or sell.

Return ONLY JSON:
{
  "topic": "...",
  "summary": "short overview",
  "how_it_works": ["...", "..."],
  "athena_usage": "how Athena uses this in the supplied context",
  "pitfalls": ["...", "..."]
}
""".strip()


def build(
    topic: IndicatorTopic | str,
    context: MarketContext | None = None,
) -> tuple[str, str]:
    topic_value = topic.value if isinstance(topic, IndicatorTopic) else str(topic)
    payload: dict = {"topic": topic_value}
    if context is not None:
        payload["market_context"] = PromptBuilder.from_market_context(context)
        payload["market_context"].pop("trade_plan", None)
    user = (
        "Indicator education request\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
