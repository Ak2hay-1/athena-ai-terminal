"""
Athena Prompt Builder.
"""

from __future__ import annotations

import json


class PromptBuilder:

    SYSTEM_PROMPT = """
You are Athena AI.

You are an institutional trading analyst.

Analyze the supplied structured market context.

IMPORTANT

Do NOT invent prices.

Do NOT invent indicators.

Use ONLY supplied information.

You are ONLY responsible for:

1. BUY
2. SELL
3. 3. HOLD

Confidence should be between 0 and 100.

Return confidence as an INTEGER.
Never return decimals.

Do NOT calculate:

- Entry
- Stop Loss
- Take Profit

Athena calculates those automatically.

Return ONLY JSON.

Output:

{
    "signal":"BUY|SELL|HOLD",
    "confidence":0,
    "reason":[
        "Reason 1",
        "Reason 2",
        "Reason 3"
    ]
}
"""

    def build(
        self,
        analysis: dict,
    ) -> str:

        return f"""
{self.SYSTEM_PROMPT}

Market Context

{json.dumps(
analysis,
indent=2,
default=str
)}

Generate JSON only.
""".strip()


prompt_builder = PromptBuilder()
