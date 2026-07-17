"""
Liquidity-first take profit calculation.
"""

from __future__ import annotations

from app.core.settings import settings
from app.risk.models import StructureContext
from app.risk.models import TakeProfitResult
from app.risk.models import TradeDirection
from app.risk.models import ZoneLevel
from app.risk.symbol_profile import get_symbol_profile
from app.risk.symbol_profile import round_price


class TakeProfitService:
    """
    Target liquidity pools; fall back to RR multiple of risk.
    """

    def calculate(
        self,
        context: StructureContext,
        direction: TradeDirection,
        *,
        entry: float,
        stop_loss: float,
        confidence: int,
    ) -> TakeProfitResult:
        profile = get_symbol_profile(context.symbol, atr=context.atr)
        risk = abs(entry - stop_loss)
        if risk <= 0:
            return TakeProfitResult(
                take_profit=entry,
                tp_reason="Invalid risk distance",
                reward_distance=0.0,
                at_liquidity=False,
                risk_reward=0.0,
            )

        target_rr = self.dynamic_rr(confidence)
        min_rr = float(settings.MIN_RR)
        max_rr = float(settings.MAX_RR)

        targets = (
            context.liquidity_targets_high
            if direction == TradeDirection.BUY
            else context.liquidity_targets_low
        )
        chosen = self._nearest_valid_target(
            targets=targets,
            direction=direction,
            entry=entry,
            risk=risk,
            min_rr=min_rr,
            max_rr=max_rr,
        )

        if chosen is not None:
            tp, zone = chosen
            tp = round_price(tp, profile.digits)
            reward = abs(tp - entry)
            rr = reward / risk if risk else 0.0
            return TakeProfitResult(
                take_profit=tp,
                tp_reason=f"Liquidity target: {zone.kind.replace('_', ' ')}",
                reward_distance=reward,
                at_liquidity=True,
                risk_reward=round(rr, 2),
            )

        # Fallback: Entry ± risk * RR
        if direction == TradeDirection.BUY:
            tp = entry + (risk * target_rr)
        else:
            tp = entry - (risk * target_rr)
        tp = round_price(tp, profile.digits)
        reward = abs(tp - entry)
        return TakeProfitResult(
            take_profit=tp,
            tp_reason=f"RR fallback ({target_rr:.2f}R); no liquidity target in band",
            reward_distance=reward,
            at_liquidity=False,
            risk_reward=round(target_rr, 2),
        )

    @staticmethod
    def dynamic_rr(confidence: int) -> float:
        min_rr = float(settings.MIN_RR)
        max_rr = float(settings.MAX_RR)
        preferred = float(settings.PREFERRED_RR)

        if confidence >= 90:
            rr = 3.0
        elif confidence >= 75:
            rr = 2.2
        elif confidence >= 60:
            rr = min_rr
        else:
            rr = min_rr

        # Blend toward preferred as confidence rises
        if 60 <= confidence < 90:
            span = (confidence - 60) / 30.0
            rr = min_rr + span * (preferred - min_rr)
            if confidence >= 75:
                rr = max(rr, 2.2)

        return max(min_rr, min(max_rr, round(rr, 2)))

    @staticmethod
    def _nearest_valid_target(
        *,
        targets: list[ZoneLevel],
        direction: TradeDirection,
        entry: float,
        risk: float,
        min_rr: float,
        max_rr: float,
    ) -> tuple[float, ZoneLevel] | None:
        best: tuple[float, ZoneLevel] | None = None
        best_dist: float | None = None

        for zone in targets:
            level = float(zone.price)
            if direction == TradeDirection.BUY:
                if level <= entry:
                    continue
                reward = level - entry
            else:
                if level >= entry:
                    continue
                reward = entry - level

            rr = reward / risk if risk else 0.0
            if rr < min_rr or rr > max_rr:
                continue

            if best_dist is None or reward < best_dist:
                best_dist = reward
                best = (level, zone)

        return best


take_profit_service = TakeProfitService()
