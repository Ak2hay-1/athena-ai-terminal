"""Unit tests for validation APPROVED / REJECTED / WAIT."""

from __future__ import annotations

from app.agents.validation.validator import validate_trade_evidence


def test_approved_when_all_thresholds_clear() -> None:
    result = validate_trade_evidence(
        technical_score=85,
        smc_score=88,
        risk_score=90,
        risk_reward=2.5,
        warnings=[],
    )
    assert result["status"] == "APPROVED"
    assert result["approval"] is True
    assert result["confluence"] >= 70
    assert result["reasons"]


def test_rejected_on_low_technical() -> None:
    result = validate_trade_evidence(
        technical_score=40,
        smc_score=90,
        risk_score=90,
        risk_reward=2.5,
        warnings=[],
    )
    assert result["status"] == "REJECTED"
    assert result["approval"] is False
    assert any("weak" in r.lower() or "technical" in r.lower() for r in result["reasons"])


def test_rejected_on_news_risk() -> None:
    result = validate_trade_evidence(
        technical_score=85,
        smc_score=85,
        risk_score=85,
        risk_reward=2.5,
        warnings=["news_risk"],
    )
    assert result["status"] == "REJECTED"
    assert "News risk" in result["reasons"]


def test_rejected_on_poor_rr() -> None:
    result = validate_trade_evidence(
        technical_score=85,
        smc_score=85,
        risk_score=85,
        risk_reward=1.0,
        warnings=[],
    )
    assert result["status"] == "REJECTED"
    assert "Poor RR" in result["reasons"]


def test_wait_on_borderline_scores() -> None:
    result = validate_trade_evidence(
        technical_score=62,
        smc_score=80,
        risk_score=80,
        risk_reward=2.0,
        warnings=[],
    )
    assert result["status"] == "WAIT"
    assert result["approval"] is False
