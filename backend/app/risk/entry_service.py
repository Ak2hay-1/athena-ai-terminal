"""
Structure-aware entry selection.
"""

from __future__ import annotations

from app.risk.models import EntryResult
from app.risk.models import EntryType
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.symbol_profile import get_symbol_profile
from app.risk.symbol_profile import round_price


class EntryService:
    """
    Prefer limit entries at OB / FVG / premium-discount over market.
    """

    def calculate(
        self,
        context: StructureContext,
        direction: TradeDirection,
        *,
        stop_loss: float | None = None,
    ) -> EntryResult:
        profile = get_symbol_profile(context.symbol, atr=context.atr)
        market = round_price(context.price, profile.digits)

        limit = self._best_limit(context, direction, market, stop_loss)
        if limit is not None:
            price, reason = limit
            price = round_price(price, profile.digits)
            if stop_loss is not None:
                if direction == TradeDirection.BUY and price <= stop_loss:
                    return EntryResult(
                        entry=market,
                        entry_type=EntryType.MARKET,
                        entry_reason="Market entry; limit would sit at/through stop",
                    )
                if direction == TradeDirection.SELL and price >= stop_loss:
                    return EntryResult(
                        entry=market,
                        entry_type=EntryType.MARKET,
                        entry_reason="Market entry; limit would sit at/through stop",
                    )
            # Only use limit if it improves vs market (BUY lower, SELL higher)
            if direction == TradeDirection.BUY and price < market:
                return EntryResult(
                    entry=price,
                    entry_type=EntryType.LIMIT,
                    entry_reason=reason,
                )
            if direction == TradeDirection.SELL and price > market:
                return EntryResult(
                    entry=price,
                    entry_type=EntryType.LIMIT,
                    entry_reason=reason,
                )

        return EntryResult(
            entry=market,
            entry_type=EntryType.MARKET,
            entry_reason="Current market price",
        )

    def _best_limit(
        self,
        context: StructureContext,
        direction: TradeDirection,
        market: float,
        stop_loss: float | None,
    ) -> tuple[float, str] | None:
        candidates: list[tuple[float, str, int]] = []

        if direction == TradeDirection.BUY:
            for ob in reversed(context.bullish_order_blocks):
                edge = float(ob.high if ob.high is not None else ob.price)
                mid = float(ob.price)
                for price, label, prio in (
                    (edge, "Limit entry at bullish order block", 3),
                    (mid, "Limit entry at order block midpoint", 2),
                ):
                    if price < market and (stop_loss is None or price > stop_loss):
                        candidates.append((price, label, prio))
            for fvg in reversed(context.bullish_fvgs):
                fill = float(fvg.high if fvg.high is not None else fvg.price)
                if fill < market and (stop_loss is None or fill > stop_loss):
                    candidates.append((fill, "Limit entry at bullish FVG", 2))
            if context.in_discount and context.equilibrium is not None:
                ote = self._ote_price(context, bullish=True)
                if ote is not None and ote < market and (stop_loss is None or ote > stop_loss):
                    candidates.append((ote, "Limit entry in discount / OTE zone", 1))
        else:
            for ob in reversed(context.bearish_order_blocks):
                edge = float(ob.low if ob.low is not None else ob.price)
                mid = float(ob.price)
                for price, label, prio in (
                    (edge, "Limit entry at bearish order block", 3),
                    (mid, "Limit entry at order block midpoint", 2),
                ):
                    if price > market and (stop_loss is None or price < stop_loss):
                        candidates.append((price, label, prio))
            for fvg in reversed(context.bearish_fvgs):
                fill = float(fvg.low if fvg.low is not None else fvg.price)
                if fill > market and (stop_loss is None or fill < stop_loss):
                    candidates.append((fill, "Limit entry at bearish FVG", 2))
            if context.in_premium and context.equilibrium is not None:
                ote = self._ote_price(context, bullish=False)
                if ote is not None and ote > market and (stop_loss is None or ote < stop_loss):
                    candidates.append((ote, "Limit entry in premium / OTE zone", 1))

        if not candidates:
            return None

        # Prefer highest priority, then closest improvement vs market
        if direction == TradeDirection.BUY:
            candidates.sort(key=lambda c: (-c[2], -c[0]))
        else:
            candidates.sort(key=lambda c: (-c[2], c[0]))
        best = candidates[0]
        return best[0], best[1]

    @staticmethod
    def _ote_price(context: StructureContext, *, bullish: bool) -> float | None:
        if context.range_high is None or context.range_low is None:
            return None
        span = context.range_high - context.range_low
        if span <= 0:
            return None
        # Optimal trade entry band ~62-79% retracement of dealing range
        if bullish:
            return context.range_low + span * 0.705
        return context.range_high - span * 0.705


entry_service = EntryService()
