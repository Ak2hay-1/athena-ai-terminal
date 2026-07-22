"""
Confidence breakdown from existing ConfidenceEngine components.

Remaps engine weights into institutional UI categories without changing
the authoritative confidence total.
"""

from __future__ import annotations

from app.core.logger import logger
from app.risk.confidence_engine import ConfidenceEngine
from app.risk.confidence_engine import confidence_engine
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.schemas.institutional import ConfidenceBreakdown


# Category maxima = sum of mapped ConfidenceEngine WEIGHTS.
CATEGORY_MAX = {
    "trend": 35,  # trend(20) + multi_tf(15)
    "momentum": 15,  # volume
    "structure": 20,  # smc
    "liquidity": 15,
    "news": 10,
    "risk": 5,  # risk_quality
}


class ConfidenceBreakdownService:
    """
    Derive a category breakdown that sums exactly to plan.confidence.
    """

    def __init__(self, engine: ConfidenceEngine | None = None) -> None:
        self._engine = engine or confidence_engine

    def build(
        self,
        context: StructureContext,
        plan: TradePlan,
    ) -> ConfidenceBreakdown:
        direction = self._direction(plan)
        if direction is None or int(plan.confidence) <= 0:
            return ConfidenceBreakdown(
                trend=0,
                momentum=0,
                structure=0,
                liquidity=0,
                news=0,
                risk=0,
                **{f"{k}_max": v for k, v in CATEGORY_MAX.items()},
            )

        structure_sl = bool(plan.validation.structure_sl)
        at_liquidity_tp = "liquidity" in (plan.tp_reason or "").lower()

        components = self._engine.score_components(
            context,
            direction,
            at_liquidity_tp=at_liquidity_tp,
            structure_sl=structure_sl,
            risk_reward=float(plan.risk_reward),
        )

        raw = {
            "trend": float(components["trend"]) + float(components["multi_tf"]),
            "momentum": float(components["volume"]),
            "structure": float(components["smc"]),
            "liquidity": float(components["liquidity"]),
            "news": float(components["news"]),
            "risk": float(components["risk_quality"]),
        }

        target = int(plan.confidence)
        allocated = self._allocate_integers(raw, target)

        breakdown = ConfidenceBreakdown(
            trend=allocated["trend"],
            momentum=allocated["momentum"],
            structure=allocated["structure"],
            liquidity=allocated["liquidity"],
            news=allocated["news"],
            risk=allocated["risk"],
            trend_max=CATEGORY_MAX["trend"],
            momentum_max=CATEGORY_MAX["momentum"],
            structure_max=CATEGORY_MAX["structure"],
            liquidity_max=CATEGORY_MAX["liquidity"],
            news_max=CATEGORY_MAX["news"],
            risk_max=CATEGORY_MAX["risk"],
        )

        total = (
            breakdown.trend
            + breakdown.momentum
            + breakdown.structure
            + breakdown.liquidity
            + breakdown.news
            + breakdown.risk
        )
        if total != target:
            logger.warning(
                "Confidence breakdown sum %s != confidence %s; correcting",
                total,
                target,
            )
            # Force exact match by adjusting largest category.
            delta = target - total
            keys = ["trend", "structure", "momentum", "liquidity", "news", "risk"]
            best = max(keys, key=lambda k: getattr(breakdown, k))
            setattr(breakdown, best, max(0, getattr(breakdown, best) + delta))

        return breakdown

    @staticmethod
    def _direction(plan: TradePlan) -> TradeDirection | None:
        signal = (plan.signal or "").upper()
        if signal == "BUY":
            return TradeDirection.BUY
        if signal == "SELL":
            return TradeDirection.SELL
        # NO_TRADE / HOLD may still have a directional trend for breakdown.
        trend = (plan.trend or "").upper()
        if trend == "BULLISH":
            return TradeDirection.BUY
        if trend == "BEARISH":
            return TradeDirection.SELL
        return None

    @staticmethod
    def _allocate_integers(raw: dict[str, float], target: int) -> dict[str, int]:
        """
        Largest-remainder allocation so ints sum exactly to target.
        """
        if target <= 0:
            return {k: 0 for k in raw}

        total_raw = sum(raw.values())
        if total_raw <= 0:
            # Spread evenly if components are empty but confidence > 0.
            base = target // len(raw)
            rem = target % len(raw)
            out = {k: base for k in raw}
            for k in list(raw.keys())[:rem]:
                out[k] += 1
            return out

        # Scale raw so sum(raw) matches target before integer allocation.
        scale = target / total_raw
        scaled = {k: v * scale for k, v in raw.items()}
        floors = {k: int(v) for k, v in scaled.items()}
        remainder = target - sum(floors.values())
        order = sorted(
            scaled.keys(),
            key=lambda k: (scaled[k] - floors[k], scaled[k]),
            reverse=True,
        )
        for k in order:
            if remainder <= 0:
                break
            floors[k] += 1
            remainder -= 1
        return floors


confidence_breakdown_service = ConfidenceBreakdownService()
