"""Strategy teacher prompt builder."""

from __future__ import annotations

import json
from enum import Enum


class StrategyTopic(str, Enum):
    SMC = "smc"
    RISK = "risk"
    FVG = "fvg"
    ORDER_BLOCKS = "order_blocks"
    LIQUIDITY = "liquidity"
    MARKET_STRUCTURE = "market_structure"
    PSYCHOLOGY = "psychology"
    MULTI_TIMEFRAME = "multi_timeframe"
    CONFLUENCE = "confluence"
    NO_TRADE = "no_trade"


SYSTEM_PROMPT = """
You are Athena AI, an institutional strategy teacher.

Teach the requested curriculum topic clearly and practically.
Athena's engines decide trades — you never invent BUY/SELL, entry, SL/TP,
confidence, or probability for a live market.

Return ONLY JSON:
{
  "topic": "...",
  "title": "...",
  "lesson": "2-4 paragraph lesson",
  "key_points": ["...", "...", "..."],
  "exercise": "one short practice question or drill",
  "common_mistakes": ["...", "..."]
}
""".strip()


def build(topic: StrategyTopic | str) -> tuple[str, str]:
    topic_value = topic.value if isinstance(topic, StrategyTopic) else str(topic)
    user = (
        "Strategy curriculum request\n\n"
        f"{json.dumps({'topic': topic_value}, indent=2)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
