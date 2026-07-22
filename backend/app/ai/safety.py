"""Safety rails for Athena AI communication layer.

AI must never invent signals, entries, SL/TP, confidence, or probability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# User intents that ask the LLM to make a trading decision.
_DECISION_PATTERNS = [
    r"\bshould\s+i\s+(buy|sell|long|short|enter|trade|hold)\b",
    r"\b(buy|sell|long|short)\s+(now|here|this|it)\b",
    r"\bwhat\s+(entry|stop\s*loss|take\s*profit|sl|tp)\b",
    r"\b(give|set|suggest|recommend)\s+(me\s+)?(an?\s+)?(entry|sl|tp|stop|target)\b",
    r"\bwhere\s+(should|do)\s+i\s+(enter|buy|sell|place)\b",
    r"\b(predict|forecast)\s+(the\s+)?(price|direction|move)\b",
    r"\bwill\s+(it|price|gold|xau)\s+(go\s+)?(up|down|rise|fall)\b",
    r"\bwhat\s+(is|should\s+be)\s+(my\s+)?(confidence|probability)\b",
    r"\bmake\s+(me\s+)?a\s+(trade|signal)\b",
    r"\bis\s+(this|it)\s+a\s+(buy|sell|long|short)\b",
]

_BANNED_RESPONSE = re.compile(
    r"(?i)\b(i\s+recommend\s+(you\s+)?(buy|sell)|"
    r"you\s+should\s+(buy|sell|enter|long|short)|"
    r"enter\s+at\s+\d|"
    r"set\s+(sl|tp|stop|take\s*profit)\s+(at|to)\s+\d)",
)

REDIRECT_MESSAGE = (
    "Athena's deterministic engine already owns the trade decision "
    "(signal, confidence, entry, SL/TP, and probability). "
    "I can only explain that frozen recommendation and the market context — "
    "I cannot invent a new trade, levels, or advice. "
    "Ask me to explain the current Athena plan, structure, risk, or indicators."
)


@dataclass(frozen=True)
class SafetyResult:
    blocked: bool
    redirect_message: str | None = None
    reason: str | None = None


def detect_decision_request(text: str) -> SafetyResult:
    """Return blocked=True when the user asks for a trading decision."""
    normalized = (text or "").strip().lower()
    if not normalized:
        return SafetyResult(blocked=False)

    for pattern in _DECISION_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return SafetyResult(
                blocked=True,
                redirect_message=REDIRECT_MESSAGE,
                reason="decision_request",
            )
    return SafetyResult(blocked=False)


def filter_response(text: str) -> str:
    """Light post-filter: soften banned advice patterns."""
    if not text:
        return text
    if _BANNED_RESPONSE.search(text):
        return (
            f"{text.strip()}\n\n"
            "Note: Athena's frozen recommendation remains authoritative; "
            "do not treat the above as a new trade signal or advice to enter."
        )
    return text


def last_user_message(messages: list) -> str:
    for message in reversed(messages):
        role = getattr(message, "role", None) or (
            message.get("role") if isinstance(message, dict) else None
        )
        content = getattr(message, "content", None) or (
            message.get("content") if isinstance(message, dict) else None
        )
        if role == "user" and content:
            return str(content)
    return ""
