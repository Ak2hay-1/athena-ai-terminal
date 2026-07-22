"""Chat prompt builder."""

from __future__ import annotations

import json

from app.ai.prompts.prompt_builder import PromptBuilder
from app.ai.schemas.context import MarketContext

SYSTEM_PROMPT = """
You are Athena AI, an institutional trading assistant.

HARD RULES (non-negotiable):
- Athena's deterministic engines ALREADY finalize signal, confidence, entry,
  stop loss, take profit, risk/reward, and probability.
- You explain and educate ONLY. You never invent or revise trade decisions.
- If the user asks "should I buy/sell?", where to enter, or for SL/TP/prediction,
  refuse to decide and redirect them to Athena's frozen recommendation.
- Advisory communication only; never claim to execute trades.
- Do NOT invent prices, indicators, or trade levels.
- If market context is provided, ground answers in that context only.
- If information is missing, say so clearly.
- Be concise and professional.
""".strip()


def build_system(context: MarketContext | None = None) -> str:
    if context is None:
        return SYSTEM_PROMPT

    payload = PromptBuilder.from_market_context(context)
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Current structured market context (JSON):\n"
        f"{json.dumps(payload, indent=2, default=str)}"
    )
