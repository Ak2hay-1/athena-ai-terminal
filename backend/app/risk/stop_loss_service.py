"""
Structure-first stop loss calculation.
"""

from __future__ import annotations

from app.core.logger import logger
from app.core.settings import settings
from app.risk.models import StopLossResult
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.symbol_profile import atr_multiplier_for
from app.risk.symbol_profile import get_symbol_profile
from app.risk.symbol_profile import round_price


class StopLossService:
    """
    Calculate invalidation-based stop losses.
    """

    def calculate(
        self,
        context: StructureContext,
        direction: TradeDirection,
        *,
        reference_price: float | None = None,
    ) -> StopLossResult:
        profile = get_symbol_profile(context.symbol, atr=context.atr)
        entry_ref = float(reference_price if reference_price is not None else context.price)
        atr = float(context.atr or 0.0)

        if not context.atr_ok or context.tight_range or atr <= 0:
            logger.info(
                "StopLoss rejected for %s: atr_ok=%s tight_range=%s atr=%s",
                context.symbol,
                context.atr_ok,
                context.tight_range,
                atr,
            )
            return StopLossResult(
                stop_loss=entry_ref,
                sl_reason="Rejected: ATR too low or market ranging tightly",
                risk_distance=0.0,
                used_structure="none",
                valid=False,
            )

        buffer = max(
            atr * float(settings.SL_BUFFER_ATR_FRACTION),
            profile.tick_size * 2,
        )
        min_distance = max(
            atr * float(settings.MIN_SL_ATR_FRACTION),
            profile.min_sl_distance,
        )

        structure_level, structure_kind = self._select_invalidation(
            context,
            direction,
            entry_ref,
        )

        if structure_level is not None:
            if direction == TradeDirection.BUY:
                stop = structure_level - buffer
                reason = f"Below {structure_kind} with ATR buffer"
            else:
                stop = structure_level + buffer
                reason = f"Above {structure_kind} with ATR buffer"
            used = structure_kind
        else:
            # ATR fallback only when no structure exists
            distance = atr * atr_multiplier_for(context.timeframe)
            if direction == TradeDirection.BUY:
                stop = entry_ref - distance
            else:
                stop = entry_ref + distance
            reason = (
                f"ATR fallback ({atr_multiplier_for(context.timeframe):.1f}x ATR); "
                "no valid structure invalidation"
            )
            used = "atr_fallback"

        stop = round_price(stop, profile.digits)
        risk = abs(entry_ref - stop)

        if risk < min_distance:
            if direction == TradeDirection.BUY:
                stop = round_price(entry_ref - min_distance, profile.digits)
            else:
                stop = round_price(entry_ref + min_distance, profile.digits)
            risk = abs(entry_ref - stop)
            reason = f"{reason}; widened to minimum SL distance"

        if risk <= 0 or (
            direction == TradeDirection.BUY and stop >= entry_ref
        ) or (
            direction == TradeDirection.SELL and stop <= entry_ref
        ):
            return StopLossResult(
                stop_loss=entry_ref,
                sl_reason="Invalid stop relative to entry",
                risk_distance=0.0,
                used_structure=used,
                valid=False,
            )

        return StopLossResult(
            stop_loss=stop,
            sl_reason=reason,
            risk_distance=risk,
            used_structure=used,
            valid=True,
        )

    def _select_invalidation(
        self,
        context: StructureContext,
        direction: TradeDirection,
        entry_ref: float,
    ) -> tuple[float | None, str]:
        """
        Priority: swing -> order block / demand-supply -> liquidity sweep.
        Prefer the furthest invalidation that still leaves room for a trade.
        """
        candidates: list[tuple[float, str, int]] = []

        if direction == TradeDirection.BUY:
            if context.swing_lows:
                level = context.swing_lows[-1]
                if level < entry_ref:
                    candidates.append((level, "latest swing low", 3))
            for ob in reversed(context.bullish_order_blocks):
                level = float(ob.low if ob.low is not None else ob.price)
                if level < entry_ref:
                    candidates.append((level, "order block / demand zone low", 2))
                    break
            if context.liquidity_sweep_lows:
                level = context.liquidity_sweep_lows[-1]
                if level < entry_ref:
                    candidates.append((level, "liquidity sweep low", 1))
            if not candidates:
                return None, "none"
            # Deepest (lowest) structure for BUY invalidation
            candidates.sort(key=lambda item: (item[0], -item[2]))
            best = candidates[0]
            return best[0], best[1]

        # SELL
        if context.swing_highs:
            level = context.swing_highs[-1]
            if level > entry_ref:
                candidates.append((level, "latest swing high", 3))
        for ob in reversed(context.bearish_order_blocks):
            level = float(ob.high if ob.high is not None else ob.price)
            if level > entry_ref:
                candidates.append((level, "supply zone / bearish order block", 2))
                break
        if context.liquidity_sweep_highs:
            level = context.liquidity_sweep_highs[-1]
            if level > entry_ref:
                candidates.append((level, "liquidity sweep high", 1))
        if not candidates:
            return None, "none"
        # Highest structure for SELL invalidation
        candidates.sort(key=lambda item: (-item[0], -item[2]))
        best = candidates[0]
        return best[0], best[1]


stop_loss_service = StopLossService()
