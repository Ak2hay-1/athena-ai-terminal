"""Unit tests for setup reasoning prompt and gate."""

from __future__ import annotations

import pytest

from app.ai.prompts.setup_reasoning import SYSTEM_PROMPT
from app.ai.prompts.setup_reasoning import build
from app.ai.reasoning import SetupReasoningEngine
from app.ai.reasoning import should_run_reasoning
from app.core.settings import settings


def test_prompt_forbids_invention_and_includes_evidence() -> None:
    assert "NEVER calculate" in SYSTEM_PROMPT or "Never invent" in SYSTEM_PROMPT
    system, user = build(
        {
            "symbol": "EURUSD",
            "confluence": 88,
            "scores": {"technical": 84, "smc": 90, "risk": 92},
        },
        {"count": 20, "win_rate": 71, "average_rr": 2.3},
    )
    assert "EURUSD" in user
    assert "71" in user or "win_rate" in user
    assert system == SYSTEM_PROMPT


def test_gate_skips_low_confluence_and_non_approved() -> None:
    assert should_run_reasoning({"status": "WAIT", "confluence": 90}) is False
    assert should_run_reasoning({"status": "APPROVED", "confluence": 50}) is False
    # May be True depending on settings defaults
    original = settings.REASONING_ENABLED
    try:
        object.__setattr__(settings, "REASONING_ENABLED", True) if hasattr(
            settings, "__dict__"
        ) else None
    except Exception:
        pass
    # Use values that clearly pass defaults
    assert (
        should_run_reasoning({"status": "APPROVED", "confluence": 95})
        is settings.REASONING_ENABLED
    )


@pytest.mark.asyncio
async def test_engine_uses_mocked_client() -> None:
    class _FakeClient:
        async def generate_json(self, **kwargs):
            return {
                "success": True,
                "data": {
                    "summary": "Bullish structure with strong confluence.",
                    "institutional_reasoning": "Liquidity sweep then continuation.",
                    "potential_risks": ["News risk"],
                    "alternative_scenarios": ["Range continuation"],
                    "confidence_explanation": "Scores are aligned.",
                    "what_to_watch": ["London open"],
                    "evidence_citations": ["confluence=88"],
                },
                "provider": "mock",
                "model": "gpt-5-mini",
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "latency_ms": 5.0,
                "cost_usd": 0.0,
            }

    engine = SetupReasoningEngine(client=_FakeClient())  # type: ignore[arg-type]
    result = await engine.reason(
        {"symbol": "EURUSD", "confluence": 88, "status": "APPROVED"},
        {"count": 12, "win_rate": 66.0},
    )
    assert result.success is True
    assert "confluence" in " ".join(result.evidence_citations).lower() or result.summary
    assert result.provider == "mock"

    # Cache hit
    cached = await engine.reason(
        {"symbol": "EURUSD", "confluence": 88, "status": "APPROVED"},
        {"count": 12, "win_rate": 66.0},
    )
    assert cached.cached is True
