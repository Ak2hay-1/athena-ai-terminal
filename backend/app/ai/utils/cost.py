"""
Rough USD cost estimates for known models.

Unknown models return None; token counts are still logged upstream.
"""

from __future__ import annotations

# (prompt_per_1m_tokens, completion_per_1m_tokens)
_MODEL_PRICES_USD: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-3-5-sonnet-latest": (3.00, 15.00),
    "deepseek-chat": (0.14, 0.28),
    "grok-2": (2.00, 10.00),
    "llama3.2": (0.0, 0.0),
    "nomic-embed-text": (0.0, 0.0),
}


def estimate_cost_usd(
    model: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> float | None:
    """Estimate cost in USD for a completed generation call."""

    prices = _MODEL_PRICES_USD.get(model)
    if prices is None:
        # Try prefix match (e.g. gemini-2.0-flash-001)
        for key, value in _MODEL_PRICES_USD.items():
            if model.startswith(key):
                prices = value
                break
    if prices is None:
        return None

    prompt = prompt_tokens or 0
    completion = completion_tokens or 0
    prompt_rate, completion_rate = prices
    return round(
        (prompt / 1_000_000) * prompt_rate
        + (completion / 1_000_000) * completion_rate,
        8,
    )
