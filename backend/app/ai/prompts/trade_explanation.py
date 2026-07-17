"""Trade explanation prompt builder."""

from __future__ import annotations

import json

from app.ai.schemas.context import MarketContext
from app.ai.utils.context_filter import assert_safe_context

SYSTEM_PROMPT = """
You are Athena AI.

You are an institutional trading analyst.

A deterministic risk engine has ALREADY calculated:
- signal
- confidence
- entry / entry_type
- stop_loss
- take_profit
- risk_reward
- sl_reason / tp_reason

IMPORTANT

Do NOT invent prices.
Do NOT invent indicators.
Do NOT recalculate Entry, Stop Loss, Take Profit, or Confidence.
Do NOT change the signal.

Use ONLY the supplied trade plan and market context.

Your ONLY job is to return short institutional reasoning that explains
why those levels make sense (or why there is NO_TRADE).

Return ONLY JSON:

{
    "reason": [
        "Reason 1",
        "Reason 2",
        "Reason 3"
    ]
}
""".strip()


def build(context: MarketContext) -> tuple[str, str]:
    """Return (system, user) prompts for trade explanation."""

    payload = assert_safe_context(
        {
            "trade_plan": (
                context.trade_candidate.model_dump()
                if context.trade_candidate
                else {}
            ),
            "market_context": {
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
            },
        }
    )
    user = (
        "Frozen Trade Plan And Market Context\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        'Generate JSON only with a "reason" array.'
    )
    return SYSTEM_PROMPT, user
