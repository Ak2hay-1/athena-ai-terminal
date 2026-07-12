"""
Prompt Builder.

Builds structured prompts for the AI model.
"""

from __future__ import annotations

import json


class PromptBuilder:
    """
    Converts market analysis into an AI prompt.
    """

    def build(
        self,
        analysis: dict,
    ) -> str:

        prompt = f"""
You are Athena AI, an institutional trading analyst.

Analyze the following market information.

Return ONLY valid JSON.

Required JSON format:

{{
    "signal":"BUY | SELL | WAIT",
    "confidence":0,
    "entry":0,
    "stop_loss":0,
    "take_profit":0,
    "risk_reward":0,
    "reason":[]
}}

Market Analysis

{json.dumps(analysis, indent=4)}

Rules

- Never hallucinate.
- Never invent prices.
- Use only supplied information.
- Confidence must be between 0 and 100.
- Reasons must be concise.
"""

        return prompt.strip()


prompt_builder = PromptBuilder()