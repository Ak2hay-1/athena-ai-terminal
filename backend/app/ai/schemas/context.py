"""
Slim market context schemas for AI prompts.

Never include OHLC candles, indicator history, or order books.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class TradeCandidate(BaseModel):
    """Frozen trade plan fields the LLM may explain."""

    signal: str = "HOLD"
    confidence: int = 0
    entry: float = 0.0
    entry_type: str = "NONE"
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_reward: float = 0.0
    risk_pips: float = 0.0
    reward_pips: float = 0.0
    sl_reason: str = ""
    tp_reason: str = ""
    entry_reason: str = ""
    reasons: list[str] = Field(default_factory=list)


class NewsItem(BaseModel):
    """Compact news item for summarization."""

    title: str
    summary: str = ""
    sentiment: str | None = None
    impact: str | None = None
    source: str | None = None


class ChatMessage(BaseModel):
    """Single chat turn."""

    role: str
    content: str


class MarketContext(BaseModel):
    """
    Structured market context sent to AI providers.

    Contains only aggregated SMC / indicator / sentiment signals.
    """

    symbol: str
    timeframe: str
    trend: str | None = None
    market_structure: dict[str, Any] = Field(default_factory=dict)
    liquidity: dict[str, Any] = Field(default_factory=dict)
    order_blocks: dict[str, Any] = Field(default_factory=dict)
    fvg: dict[str, Any] = Field(default_factory=dict)
    volume: dict[str, Any] = Field(default_factory=dict)
    momentum: dict[str, Any] = Field(default_factory=dict)
    volatility: dict[str, Any] = Field(default_factory=dict)
    sentiment: dict[str, Any] = Field(default_factory=dict)
    news_summary: str | None = None
    confluence: dict[str, Any] = Field(default_factory=dict)
    multi_timeframe: dict[str, Any] = Field(default_factory=dict)
    trade_candidate: TradeCandidate | None = None
    price: float | None = None

    @classmethod
    def from_analysis(
        cls,
        analysis: dict[str, Any],
        *,
        symbol: str,
        timeframe: str,
        trade_plan: dict[str, Any] | None = None,
    ) -> MarketContext:
        """Build slim context from market_analyzer output + optional trade plan."""

        trend_block = analysis.get("trend") or {}
        smart = analysis.get("smart_money") or {}
        indicators = analysis.get("indicators") or {}
        market = analysis.get("market") or {}
        news = analysis.get("news") or {}
        confluence = analysis.get("confluence") or {}
        multi_tf = analysis.get("multi_timeframe") or {}

        macd = indicators.get("macd") or {}
        bos = smart.get("bos") or {}
        choch = smart.get("choch") or {}

        candidate: TradeCandidate | None = None
        if trade_plan:
            candidate = TradeCandidate(
                signal=str(trade_plan.get("signal") or "HOLD"),
                confidence=int(trade_plan.get("confidence") or 0),
                entry=float(trade_plan.get("entry") or 0.0),
                entry_type=str(trade_plan.get("entry_type") or "NONE"),
                stop_loss=float(trade_plan.get("stop_loss") or 0.0),
                take_profit=float(trade_plan.get("take_profit") or 0.0),
                risk_reward=float(trade_plan.get("risk_reward") or 0.0),
                risk_pips=float(trade_plan.get("risk_pips") or 0.0),
                reward_pips=float(trade_plan.get("reward_pips") or 0.0),
                sl_reason=str(trade_plan.get("sl_reason") or ""),
                tp_reason=str(trade_plan.get("tp_reason") or ""),
                entry_reason=str(trade_plan.get("entry_reason") or ""),
                reasons=[
                    str(item)
                    for item in (trade_plan.get("reasons") or [])
                    if str(item).strip()
                ],
            )

        news_summary: str | None = None
        if isinstance(news, dict):
            news_summary = news.get("summary") or news.get("headline")
            if news_summary is not None:
                news_summary = str(news_summary)

        return cls(
            symbol=symbol,
            timeframe=timeframe,
            trend=trend_block.get("direction"),
            market_structure={
                "bos_active": bool(bos.get("active")),
                "bos_direction": bos.get("direction"),
                "choch_active": bool(choch.get("active")),
                "choch_direction": choch.get("direction"),
                "premium": bool(smart.get("premium")),
                "discount": bool(smart.get("discount")),
            },
            liquidity={
                "buy_liquidity": bool(smart.get("buy_liquidity")),
                "sell_liquidity": bool(smart.get("sell_liquidity")),
                "equal_high": bool(smart.get("equal_high")),
                "equal_low": bool(smart.get("equal_low")),
            },
            order_blocks={
                "active": bool(smart.get("order_block")),
            },
            fvg={
                "active": bool(smart.get("fair_value_gap")),
            },
            volume={
                "latest": market.get("volume"),
            },
            momentum={
                "rsi": indicators.get("rsi"),
                "macd_bullish": bool(macd.get("bullish")),
                "macd_value": macd.get("value"),
                "macd_signal": macd.get("signal"),
            },
            volatility={
                "atr": indicators.get("atr"),
            },
            sentiment={
                "news": news if isinstance(news, dict) else {},
            },
            news_summary=news_summary,
            confluence={
                "score": confluence.get("score"),
                "factors": confluence.get("factors"),
            },
            multi_timeframe=multi_tf if isinstance(multi_tf, dict) else {},
            trade_candidate=candidate,
            price=float(market["price"]) if market.get("price") is not None else None,
        )

    def cache_state(self) -> dict[str, Any]:
        """Canonical state used for Redis cache keys."""

        candidate = self.trade_candidate
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "signal": candidate.signal if candidate else None,
            "confidence": candidate.confidence if candidate else None,
            "trend": self.trend,
            "structure": self.market_structure,
            "liquidity": self.liquidity,
            "order_blocks": self.order_blocks,
            "fvg": self.fvg,
            "momentum": self.momentum,
            "volatility": self.volatility,
            "sentiment": self.sentiment,
            "confluence": self.confluence.get("score"),
            "news_summary": self.news_summary,
        }
