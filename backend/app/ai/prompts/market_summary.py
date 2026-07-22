"""Market summary prompt builder."""

from __future__ import annotations

import json

from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.schemas.context import MarketContext

SYSTEM_PROMPT = """
You are Athena AI, an institutional market desk analyst.

Summarize the supplied structured market context.
Do NOT invent prices, candles, or indicators.
Do NOT recommend specific entry/stop/take-profit levels unless present in context.
Do NOT invent a BUY/SELL signal — Athena already decides that separately.

Return ONLY JSON:
{
  "summary": "2-4 sentence overview",
  "bullets": ["point 1", "point 2", "point 3"],
  "bias": "BULLISH|BEARISH|NEUTRAL|MIXED",
  "sections": {
    "trend": "...",
    "structure": "...",
    "momentum": "...",
    "liquidity": "...",
    "risk": "..."
  }
}
""".strip()


def build(context: MarketContext) -> tuple[str, str]:
    payload = PromptBuilder.from_market_context(context)
    # Market summary should not lean on a trade plan as a decision source.
    payload.pop("trade_plan", None)
    user = (
        "Structured Market Context\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
