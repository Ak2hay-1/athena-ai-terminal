"""Market summary prompt builder."""

from __future__ import annotations

import json

from app.ai.schemas.context import MarketContext
from app.ai.utils.context_filter import assert_safe_context

SYSTEM_PROMPT = """
You are Athena AI, an institutional market desk analyst.

Summarize the supplied structured market context.
Do NOT invent prices, candles, or indicators.
Do NOT recommend specific entry/stop/take-profit levels unless present in context.

Return ONLY JSON:
{
  "summary": "2-4 sentence overview",
  "bullets": ["point 1", "point 2", "point 3"],
  "bias": "BULLISH|BEARISH|NEUTRAL|MIXED"
}
""".strip()


def build(context: MarketContext) -> tuple[str, str]:
    payload = assert_safe_context(
        {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "trend": context.trend,
            "market_structure": context.market_structure,
            "liquidity": context.liquidity,
            "order_blocks": context.order_blocks,
            "fvg": context.fvg,
            "volume": context.volume,
            "momentum": context.momentum,
            "volatility": context.volatility,
            "sentiment": context.sentiment,
            "news_summary": context.news_summary,
            "confluence": context.confluence,
            "multi_timeframe": context.multi_timeframe,
            "price": context.price,
        }
    )
    user = (
        "Structured Market Context\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
