"""News summary prompt builder."""

from __future__ import annotations

import json

from app.ai.schemas.context import MarketContext
from app.ai.schemas.context import NewsItem
from app.ai.utils.context_filter import assert_safe_context

SYSTEM_PROMPT = """
You are Athena AI, summarizing market-moving news for traders.

Use ONLY the provided headlines/items.
Do NOT invent events or prices.

Return ONLY JSON:
{
  "summary": "short paragraph",
  "bullets": ["bullet 1", "bullet 2"],
  "overall_sentiment": "BULLISH|BEARISH|NEUTRAL|MIXED"
}
""".strip()


def build(
    items: list[NewsItem],
    context: MarketContext | None = None,
) -> tuple[str, str]:
    payload = assert_safe_context(
        {
            "symbol": context.symbol if context else None,
            "timeframe": context.timeframe if context else None,
            "items": [item.model_dump() for item in items],
        }
    )
    user = (
        "News Items\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
