"""
Institutional checklist derived from validation flags and structure context.
"""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.schemas.institutional import ChecklistItem


class InstitutionalChecklistService:
    """
    Fixed-order institutional gates. Every item comes from existing analysis.
    """

    def build(
        self,
        context: StructureContext,
        plan: TradePlan,
    ) -> list[ChecklistItem]:
        flags = plan.validation
        direction = self._direction(plan)
        want = "bullish" if direction == TradeDirection.BUY else "bearish"

        htf = (context.multi_tf_trend or "").upper()
        if direction == TradeDirection.BUY:
            htf_ok = htf == "BULLISH" or (not htf and flags.trend)
        elif direction == TradeDirection.SELL:
            htf_ok = htf == "BEARISH" or (not htf and flags.trend)
        else:
            htf_ok = False

        if direction == TradeDirection.BUY:
            has_sweep = bool(context.liquidity_sweep_lows)
            has_ob = bool(context.bullish_order_blocks)
            has_fvg = bool(context.bullish_fvgs)
        elif direction == TradeDirection.SELL:
            has_sweep = bool(context.liquidity_sweep_highs)
            has_ob = bool(context.bearish_order_blocks)
            has_fvg = bool(context.bearish_fvgs)
        else:
            has_sweep = bool(context.liquidity_sweep_lows or context.liquidity_sweep_highs)
            has_ob = bool(context.bullish_order_blocks or context.bearish_order_blocks)
            has_fvg = bool(context.bullish_fvgs or context.bearish_fvgs)

        bos_ok = bool(flags.bos) or (
            context.bos_active
            and str(context.bos_direction or "").lower() == want
            and direction is not None
        )
        choch_ok = bool(flags.choch) or (
            context.choch_active
            and str(context.choch_direction or "").lower() == want
            and direction is not None
        )

        return [
            ChecklistItem(name="Higher Timeframe Trend", passed=htf_ok),
            ChecklistItem(name="BOS Confirmed", passed=bos_ok),
            ChecklistItem(name="CHOCH Confirmed", passed=choch_ok),
            ChecklistItem(name="Liquidity Sweep", passed=has_sweep),
            ChecklistItem(name="Order Block", passed=has_ob),
            ChecklistItem(name="Fair Value Gap", passed=has_fvg),
            ChecklistItem(name="ATR Validation", passed=bool(flags.atr)),
            ChecklistItem(name="Risk Reward", passed=bool(flags.risk_reward)),
            ChecklistItem(name="News Filter", passed=bool(flags.news)),
        ]

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


institutional_checklist_service = InstitutionalChecklistService()
