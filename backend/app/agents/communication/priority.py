"""
Map events and outcomes to notification priority.
"""

from __future__ import annotations

from typing import Any


def resolve_priority(event_type: str, payload: dict[str, Any]) -> str:
    et = str(event_type)
    if payload.get("sl_hit"):
        return "Critical"
    if et == "TradeClosed" and payload.get("tp_hit"):
        return "High"
    if et == "TradeClosed" and float(payload.get("pnl") or 0) < 0:
        return "High"
    if et == "TradeValidationCompleted":
        status = str(payload.get("status") or "").upper()
        confluence = float(payload.get("confluence") or 0)
        if status == "APPROVED" and confluence >= 85:
            return "High"
        return "Medium"
    if et == "WatchlistOpportunityDetected":
        return "High"
    if et == "NewsAnalysisCompleted":
        summary = payload.get("summary") or {}
        high = int(summary.get("high_impact") or summary.get("high") or 0)
        if high > 0 or str(payload.get("impact") or "").lower() == "high":
            return "High"
        return "Medium"
    if et == "PortfolioUpdated":
        health = float(payload.get("health_score") or 100)
        if health < 40:
            return "Critical"
        if health < 55:
            return "High"
        return "Low"
    if et == "LearningCompleted":
        return "Low"
    return "Medium"


def message_type_for(event_type: str, payload: dict[str, Any]) -> str:
    if payload.get("sl_hit"):
        return "SL Hit"
    if payload.get("tp_hit"):
        return "TP Hit"
    et = str(event_type)
    mapping = {
        "TradeValidationCompleted": "Trade Signal",
        "TradeClosed": "Trade Closed",
        "PortfolioUpdated": "Portfolio Update",
        "WatchlistOpportunityDetected": "Market Alert",
        "NewsAnalysisCompleted": "Breaking News",
        "LearningCompleted": "Daily Summary",
    }
    return mapping.get(et, "Market Alert")
