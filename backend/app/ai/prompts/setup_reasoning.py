"""
Setup reasoning prompt — interpret evidence only; never invent calculations.
"""

from __future__ import annotations

import json
from typing import Any

from app.ai.utils.context_filter import assert_safe_context

SYSTEM_PROMPT = """
You are Athena AI, an institutional trading evidence interpreter.

You NEVER calculate indicators, BOS, FVG, ATR, RR, stop loss, or take profit.
You ONLY interpret the structured evidence provided.

Rules:
- Use ONLY fields present in the evidence payload.
- Never invent prices, scores, or historical statistics.
- If evidence is missing, say so explicitly.
- Always reference concrete evidence fields in your explanation.

Return ONLY JSON:
{
  "summary": "what is happening",
  "institutional_reasoning": "likely institutional behaviour",
  "potential_risks": ["risk 1", "risk 2"],
  "alternative_scenarios": ["scenario 1"],
  "confidence_explanation": "why confidence is high/low based on evidence",
  "what_to_watch": ["watch item 1"],
  "evidence_citations": ["field or fact cited"]
}
""".strip()


def build(
    evidence: dict[str, Any],
    similar_trades: dict[str, Any] | None = None,
) -> tuple[str, str]:
    payload = assert_safe_context(
        {
            "evidence": evidence,
            "similar_trades": similar_trades or {},
            "instructions": [
                "Explain what is happening.",
                "Why this setup is interesting.",
                "What could invalidate it.",
                "What institutional behaviour is likely occurring.",
                "What traders should watch next.",
            ],
        }
    )
    user = (
        "Structured Evidence\n\n"
        f"{json.dumps(payload, indent=2, default=str)}\n\n"
        "Interpret the evidence. Return JSON only. Do not invent numbers."
    )
    return SYSTEM_PROMPT, user
