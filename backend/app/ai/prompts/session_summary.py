"""Session summary prompt builder."""

from __future__ import annotations

import json

from app.ai.prompts.prompt_builder import PromptBuilder

SYSTEM_PROMPT = """
You are Athena AI, summarizing a trading session.

Use ONLY the supplied stats and recommendation history.
Do NOT invent trades, P&L, or new signals.
Do NOT advise opening new positions.

Return ONLY JSON:
{
  "summary": "2-4 sentence session wrap",
  "highlights": ["...", "..."],
  "risk_notes": ["...", "..."],
  "lessons": ["...", "..."]
}
""".strip()


def build(stats: dict) -> tuple[str, str]:
    payload = PromptBuilder.from_session_stats(stats)
    user = (
        "Session stats\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Return JSON only."
    )
    return SYSTEM_PROMPT, user
