"""
Deterministic confidence scoring (not LLM).
"""

from __future__ import annotations

from app.core.settings import settings
from app.risk.models import StructureContext
from app.risk.models import TradeDirection


class ConfidenceEngine:
    """
    Weighted institutional confidence score out of 100.
    """

    WEIGHTS = {
        "trend": 20,
        "smc": 20,
        "liquidity": 15,
        "volume": 15,
        "multi_tf": 15,
        "news": 10,
        "risk_quality": 5,
    }

    def score(
        self,
        context: StructureContext,
        direction: TradeDirection,
        *,
        at_liquidity_tp: bool = False,
        structure_sl: bool = False,
        risk_reward: float = 0.0,
    ) -> int:
        total = 0
        total += self._trend_score(context, direction)
        total += self._smc_score(context, direction)
        total += self._liquidity_score(context, direction, at_liquidity_tp)
        total += self._volume_score(context)
        total += self._multi_tf_score(context, direction)
        total += self._news_score(context, direction)
        total += self._risk_quality_score(
            structure_sl=structure_sl,
            risk_reward=risk_reward,
            at_liquidity_tp=at_liquidity_tp,
        )
        return max(0, min(100, int(round(total))))

    def _trend_score(
        self,
        context: StructureContext,
        direction: TradeDirection,
    ) -> float:
        max_w = self.WEIGHTS["trend"]
        if direction == TradeDirection.BUY and context.trend == "BULLISH":
            return max_w
        if direction == TradeDirection.SELL and context.trend == "BEARISH":
            return max_w
        if context.trend == "SIDEWAYS":
            return max_w * 0.25
        return 0.0

    def _smc_score(
        self,
        context: StructureContext,
        direction: TradeDirection,
    ) -> float:
        max_w = self.WEIGHTS["smc"]
        score = 0.0
        want = "bullish" if direction == TradeDirection.BUY else "bearish"

        if context.bos_active and str(context.bos_direction or "").lower() == want:
            score += max_w * 0.45
        if context.choch_active and str(context.choch_direction or "").lower() == want:
            score += max_w * 0.35

        has_ob = (
            bool(context.bullish_order_blocks)
            if direction == TradeDirection.BUY
            else bool(context.bearish_order_blocks)
        )
        if has_ob:
            score += max_w * 0.20

        return min(max_w, score)

    def _liquidity_score(
        self,
        context: StructureContext,
        direction: TradeDirection,
        at_liquidity_tp: bool,
    ) -> float:
        max_w = self.WEIGHTS["liquidity"]
        score = 0.0
        if direction == TradeDirection.BUY:
            if context.liquidity_targets_high:
                score += max_w * 0.5
            if context.liquidity_sweep_lows:
                score += max_w * 0.3
        else:
            if context.liquidity_targets_low:
                score += max_w * 0.5
            if context.liquidity_sweep_highs:
                score += max_w * 0.3
        if at_liquidity_tp:
            score += max_w * 0.2
        return min(max_w, score)

    def _volume_score(self, context: StructureContext) -> float:
        max_w = self.WEIGHTS["volume"]
        if context.avg_volume <= 0:
            return max_w * 0.4
        ratio = context.volume / context.avg_volume
        min_ratio = float(settings.VOLUME_MIN_RATIO)
        if ratio >= 1.2:
            return max_w
        if ratio >= min_ratio:
            return max_w * 0.7
        if ratio >= min_ratio * 0.7:
            return max_w * 0.35
        return 0.0

    def _multi_tf_score(
        self,
        context: StructureContext,
        direction: TradeDirection,
    ) -> float:
        max_w = self.WEIGHTS["multi_tf"]
        mtf = (context.multi_tf_trend or "").upper()
        if not mtf:
            return max_w * 0.4
        if direction == TradeDirection.BUY and mtf == "BULLISH":
            return max_w
        if direction == TradeDirection.SELL and mtf == "BEARISH":
            return max_w
        if mtf == "SIDEWAYS":
            return max_w * 0.3
        return 0.0

    def _news_score(
        self,
        context: StructureContext,
        direction: TradeDirection,
    ) -> float:
        max_w = self.WEIGHTS["news"]
        if context.news_high_impact:
            return 0.0
        sentiment = context.news_sentiment
        if sentiment is None:
            return max_w * 0.6
        if direction == TradeDirection.BUY and sentiment > 0:
            return max_w
        if direction == TradeDirection.SELL and sentiment < 0:
            return max_w
        if abs(sentiment) < 0.1:
            return max_w * 0.5
        return max_w * 0.2

    def _risk_quality_score(
        self,
        *,
        structure_sl: bool,
        risk_reward: float,
        at_liquidity_tp: bool,
    ) -> float:
        max_w = self.WEIGHTS["risk_quality"]
        score = 0.0
        if structure_sl:
            score += max_w * 0.4
        if risk_reward >= float(settings.PREFERRED_RR):
            score += max_w * 0.4
        elif risk_reward >= float(settings.MIN_RR):
            score += max_w * 0.25
        if at_liquidity_tp:
            score += max_w * 0.2
        return min(max_w, score)


confidence_engine = ConfidenceEngine()
