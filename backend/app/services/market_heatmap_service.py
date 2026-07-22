"""
Market heatmap: normalize existing engine outputs to 0–100 visual scores.
"""

from __future__ import annotations

from typing import Any

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.schemas.institutional import MarketHeatmap


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


class MarketHeatmapService:
    """
    Visual factor scores derived from StructureContext + analysis snapshot.
    Does not invent new trading calculations.
    """

    def build(
        self,
        context: StructureContext,
        plan: TradePlan,
        analysis: dict[str, Any] | None = None,
    ) -> MarketHeatmap:
        analysis = analysis or {}
        direction = self._direction(plan)
        indicators = analysis.get("indicators") or {}
        if not isinstance(indicators, dict):
            indicators = {}

        return MarketHeatmap(
            trend=self._trend_score(context, direction),
            momentum=self._momentum_score(context, direction, indicators),
            structure=self._structure_score(context, direction),
            liquidity=self._liquidity_score(context, direction),
            volatility=self._volatility_score(context),
            news=self._news_score(context, direction),
            risk=self._risk_score(plan),
        )

    def _trend_score(
        self,
        context: StructureContext,
        direction: TradeDirection | None,
    ) -> int:
        score = 40.0
        trend = (context.trend or "").upper()
        mtf = (context.multi_tf_trend or "").upper()

        if direction == TradeDirection.BUY:
            if trend == "BULLISH":
                score += 30
            elif trend == "SIDEWAYS":
                score += 5
            if mtf == "BULLISH":
                score += 30
            elif not mtf:
                score += 12
            elif mtf == "SIDEWAYS":
                score += 8
        elif direction == TradeDirection.SELL:
            if trend == "BEARISH":
                score += 30
            elif trend == "SIDEWAYS":
                score += 5
            if mtf == "BEARISH":
                score += 30
            elif not mtf:
                score += 12
            elif mtf == "SIDEWAYS":
                score += 8
        else:
            if trend in {"BULLISH", "BEARISH"}:
                score = 50
            else:
                score = 35

        return _clamp(score)

    def _momentum_score(
        self,
        context: StructureContext,
        direction: TradeDirection | None,
        indicators: dict[str, Any],
    ) -> int:
        score = 0.0

        rsi = indicators.get("rsi")
        if rsi is None and isinstance(indicators.get("rsi_14"), (int, float)):
            rsi = indicators["rsi_14"]
        if isinstance(rsi, (int, float)):
            # Distance from 50, capped; direction-aware.
            dist = abs(float(rsi) - 50.0)
            aligned = True
            if direction == TradeDirection.BUY and float(rsi) < 50:
                aligned = False
            if direction == TradeDirection.SELL and float(rsi) > 50:
                aligned = False
            score += min(40.0, dist * 1.2) * (1.0 if aligned else 0.35)
        else:
            score += 20.0

        macd = indicators.get("macd")
        macd_bullish = None
        if isinstance(macd, dict):
            macd_bullish = macd.get("bullish")
        elif "macd_bullish" in indicators:
            macd_bullish = indicators.get("macd_bullish")
        if macd_bullish is True and direction == TradeDirection.BUY:
            score += 30
        elif macd_bullish is False and direction == TradeDirection.SELL:
            score += 30
        elif macd_bullish is not None:
            score += 8
        else:
            score += 15

        if context.avg_volume > 0:
            ratio = context.volume / context.avg_volume
            score += min(30.0, max(0.0, ratio * 20.0))
        else:
            score += 12

        return _clamp(score)

    def _structure_score(
        self,
        context: StructureContext,
        direction: TradeDirection | None,
    ) -> int:
        score = 20.0
        want = "bullish" if direction == TradeDirection.BUY else "bearish"

        if context.bos_active:
            if direction and str(context.bos_direction or "").lower() == want:
                score += 25
            else:
                score += 8
        if context.choch_active:
            if direction and str(context.choch_direction or "").lower() == want:
                score += 20
            else:
                score += 6

        if direction == TradeDirection.BUY:
            if context.bullish_order_blocks:
                score += 18
            if context.bullish_fvgs:
                score += 17
        elif direction == TradeDirection.SELL:
            if context.bearish_order_blocks:
                score += 18
            if context.bearish_fvgs:
                score += 17
        else:
            if context.bullish_order_blocks or context.bearish_order_blocks:
                score += 12
            if context.bullish_fvgs or context.bearish_fvgs:
                score += 10

        return _clamp(score)

    def _liquidity_score(
        self,
        context: StructureContext,
        direction: TradeDirection | None,
    ) -> int:
        score = 25.0
        if direction == TradeDirection.BUY:
            if context.liquidity_sweep_lows:
                score += 25
            if context.liquidity_targets_high:
                score += 25
            if context.in_discount:
                score += 25
        elif direction == TradeDirection.SELL:
            if context.liquidity_sweep_highs:
                score += 25
            if context.liquidity_targets_low:
                score += 25
            if context.in_premium:
                score += 25
        else:
            if context.liquidity_sweep_lows or context.liquidity_sweep_highs:
                score += 20
            if context.liquidity_targets_high or context.liquidity_targets_low:
                score += 20
        return _clamp(score)

    def _volatility_score(self, context: StructureContext) -> int:
        if context.tight_range or not context.atr_ok:
            return 25
        if context.atr <= 0:
            return 30
        # ATR present and healthy → mid-high volatility usefulness score.
        # Higher ATR relative to price → higher volatility reading.
        if context.price > 0:
            atr_pct = (context.atr / context.price) * 100.0
            # Typical FX ~0.05–0.3%; gold higher. Normalize softly.
            return _clamp(min(95.0, 35.0 + atr_pct * 120.0))
        return 50

    def _news_score(
        self,
        context: StructureContext,
        direction: TradeDirection | None,
    ) -> int:
        if context.news_high_impact:
            return 15
        sentiment = context.news_sentiment
        if sentiment is None:
            return 55
        mag = min(1.0, abs(float(sentiment)))
        base = 45.0 + mag * 40.0
        if direction == TradeDirection.BUY and sentiment > 0:
            return _clamp(base + 10)
        if direction == TradeDirection.SELL and sentiment < 0:
            return _clamp(base + 10)
        if abs(float(sentiment)) < 0.1:
            return 50
        return _clamp(base * 0.6)

    def _risk_score(self, plan: TradePlan) -> int:
        flags = plan.validation
        score = 20.0
        if flags.structure_sl:
            score += 20
        if flags.risk_reward:
            score += 25
        if flags.atr:
            score += 15
        if flags.risk_distance:
            score += 10
        rr = float(plan.risk_reward or 0)
        if rr >= 2.0:
            score += 10
        elif rr >= 1.5:
            score += 5
        return _clamp(score)

    @staticmethod
    def _direction(plan: TradePlan) -> TradeDirection | None:
        signal = (plan.signal or "").upper()
        if signal == "BUY":
            return TradeDirection.BUY
        if signal == "SELL":
            return TradeDirection.SELL
        trend = (plan.trend or "").upper()
        if trend == "BULLISH":
            return TradeDirection.BUY
        if trend == "BEARISH":
            return TradeDirection.SELL
        return None


market_heatmap_service = MarketHeatmapService()
