"""Chat prompt builder."""

from __future__ import annotations

import json

from app.ai.schemas.context import MarketContext
from app.ai.utils.context_filter import assert_safe_context

SYSTEM_PROMPT = """
You are Athena AI, an institutional trading assistant.

Rules:
- Advisory only; never claim to execute trades.
- Do NOT invent prices, indicators, or trade levels.
- If market context is provided, ground answers in that context only.
- If information is missing, say so clearly.
- Be concise and professional.
""".strip()


def build_system(context: MarketContext | None = None) -> str:
    if context is None:
        return SYSTEM_PROMPT

    payload = assert_safe_context(
        {
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "trend": context.trend,
            "market_structure": context.market_structure,
            "liquidity": context.liquidity,
            "order_blocks": context.order_blocks,
            "fvg": context.fvg,
            "momentum": context.momentum,
            "volatility": context.volatility,
            "sentiment": context.sentiment,
            "news_summary": context.news_summary,
            "confluence": context.confluence,
            "trade_candidate": (
                context.trade_candidate.model_dump()
                if context.trade_candidate
                else None
            ),
            "price": context.price,
        }
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Current structured market context (JSON):\n"
        f"{json.dumps(payload, indent=2, default=str)}"
    )
