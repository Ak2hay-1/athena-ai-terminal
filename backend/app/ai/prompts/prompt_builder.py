"""Serialize frozen Athena outputs for LLM prompts (never compute decisions)."""

from __future__ import annotations

from typing import Any

from app.ai.schemas.context import MarketContext
from app.ai.utils.context_filter import assert_safe_context


class PromptBuilder:
    """Converts finalized Athena artefacts into sanitized prompt payloads."""

    @staticmethod
    def from_market_context(context: MarketContext) -> dict[str, Any]:
        return assert_safe_context(
            {
                "symbol": context.symbol,
                "timeframe": context.timeframe,
                "trend": context.trend,
                "market_structure": context.market_structure,
                "liquidity": context.liquidity,
                "order_blocks": context.order_blocks,
                "fvg": context.fvg,
                "volume": context.volume,
                "momentum": context.momentum,
                "volatility": context.volatility,
                "sentiment": context.sentiment,
                "news_summary": context.news_summary,
                "confluence": context.confluence,
                "multi_timeframe": context.multi_timeframe,
                "price": context.price,
                "trade_plan": (
                    context.trade_candidate.model_dump()
                    if context.trade_candidate
                    else None
                ),
            }
        )

    @staticmethod
    def from_recommendation_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
        """Serialize a frozen recommendation dict (API / DB row dump)."""
        allowed = {
            "id": snapshot.get("id"),
            "symbol": snapshot.get("symbol"),
            "timeframe": snapshot.get("timeframe"),
            "signal": snapshot.get("signal"),
            "confidence": snapshot.get("confidence"),
            "entry_price": snapshot.get("entry_price"),
            "entry_type": snapshot.get("entry_type"),
            "stop_loss": snapshot.get("stop_loss"),
            "take_profit": snapshot.get("take_profit"),
            "risk_reward": snapshot.get("risk_reward"),
            "sl_reason": snapshot.get("sl_reason"),
            "tp_reason": snapshot.get("tp_reason"),
            "reason": snapshot.get("reason"),
            "status": snapshot.get("status"),
            "trade_probability": snapshot.get("trade_probability"),
            "trade_quality": snapshot.get("trade_quality"),
            "confidence_breakdown": snapshot.get("confidence_breakdown"),
            "institutional_checklist": snapshot.get("institutional_checklist"),
            "created_at": snapshot.get("created_at"),
        }
        return assert_safe_context(allowed)

    @staticmethod
    def from_session_stats(stats: dict[str, Any]) -> dict[str, Any]:
        return assert_safe_context(
            {
                "mode": stats.get("mode"),
                "symbol": stats.get("symbol"),
                "timeframe": stats.get("timeframe"),
                "total_recommendations": stats.get("total_recommendations"),
                "signals": stats.get("signals"),
                "avg_confidence": stats.get("avg_confidence"),
                "win_rate": stats.get("win_rate"),
                "started_at": stats.get("started_at"),
                "ended_at": stats.get("ended_at"),
                "notes": stats.get("notes"),
                "recommendations": stats.get("recommendations"),
            }
        )

    @staticmethod
    def from_analysis_dict(analysis: dict[str, Any]) -> dict[str, Any]:
        return assert_safe_context(analysis)
