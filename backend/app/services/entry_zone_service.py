"""
Smart entry zones from ATR, order blocks, FVG, and liquidity structure.
"""

from __future__ import annotations

from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.risk.models import ZoneLevel
from app.risk.symbol_profile import get_symbol_profile
from app.risk.symbol_profile import round_price
from app.schemas.institutional import EntryZone


class EntryZoneService:
    """
    Build aggressive / optimal / conservative entry prices from real levels.

    Never invents prices outside known structure + ATR geometry around
    the authoritative risk-engine entry.
    """

    def build(
        self,
        context: StructureContext,
        plan: TradePlan,
    ) -> EntryZone:
        entry = float(plan.entry or 0.0)
        if entry <= 0:
            return EntryZone()

        profile = get_symbol_profile(context.symbol, atr=context.atr)
        atr = float(context.atr or 0.0)
        direction = self._direction(plan)

        if direction is None:
            px = round_price(entry, profile.digits)
            return EntryZone(
                aggressive=px,
                optimal_low=px,
                optimal_high=px,
                conservative=px,
            )

        zone = self._primary_zone(context, direction)
        ote = self._ote_price(context, bullish=direction == TradeDirection.BUY)

        if direction == TradeDirection.BUY:
            return self._buy_zone(entry, atr, zone, ote, context.price, profile.digits)
        return self._sell_zone(entry, atr, zone, ote, context.price, profile.digits)

    def _buy_zone(
        self,
        entry: float,
        atr: float,
        zone: ZoneLevel | None,
        ote: float | None,
        market: float,
        digits: int,
    ) -> EntryZone:
        # Aggressive: nearer market (higher for buys).
        aggressive = entry
        if zone is not None and zone.high is not None:
            aggressive = max(entry, float(zone.high))
        elif atr > 0:
            aggressive = min(market, entry + atr * 0.15) if market > 0 else entry

        # Optimal band from OB/FVG high-low, else entry ± ATR fraction.
        if zone is not None and zone.high is not None and zone.low is not None:
            optimal_high = float(zone.high)
            optimal_low = float(zone.low)
        elif zone is not None:
            mid = float(zone.price)
            half = atr * 0.15 if atr > 0 else abs(mid) * 0.0001
            optimal_low = mid - half
            optimal_high = mid + half
        elif atr > 0:
            optimal_low = entry - atr * 0.25
            optimal_high = entry + atr * 0.1
        else:
            optimal_low = entry
            optimal_high = entry

        # Conservative: deeper (lower) — OTE or OB midpoint / low.
        conservative = entry
        if ote is not None and ote < entry:
            conservative = ote
        elif zone is not None and zone.low is not None:
            conservative = float(zone.low)
        elif zone is not None:
            conservative = float(zone.price)
        elif atr > 0:
            conservative = entry - atr * 0.4

        # Ensure ordering for buys: conservative <= optimal_low <= optimal_high <= aggressive
        # (or at least conservative <= entry-ish <= aggressive)
        levels = sorted([conservative, optimal_low, optimal_high, aggressive])
        conservative, optimal_low, optimal_high, aggressive = levels

        # Anchor optimal band around authoritative entry when possible.
        if optimal_low > entry:
            optimal_low = min(entry, optimal_high)
        if optimal_high < entry:
            optimal_high = max(entry, optimal_low)

        return EntryZone(
            aggressive=round_price(aggressive, digits),
            optimal_low=round_price(optimal_low, digits),
            optimal_high=round_price(optimal_high, digits),
            conservative=round_price(conservative, digits),
        )

    def _sell_zone(
        self,
        entry: float,
        atr: float,
        zone: ZoneLevel | None,
        ote: float | None,
        market: float,
        digits: int,
    ) -> EntryZone:
        aggressive = entry
        if zone is not None and zone.low is not None:
            aggressive = min(entry, float(zone.low))
        elif atr > 0:
            aggressive = max(market, entry - atr * 0.15) if market > 0 else entry

        if zone is not None and zone.high is not None and zone.low is not None:
            optimal_high = float(zone.high)
            optimal_low = float(zone.low)
        elif zone is not None:
            mid = float(zone.price)
            half = atr * 0.15 if atr > 0 else abs(mid) * 0.0001
            optimal_low = mid - half
            optimal_high = mid + half
        elif atr > 0:
            optimal_low = entry - atr * 0.1
            optimal_high = entry + atr * 0.25
        else:
            optimal_low = entry
            optimal_high = entry

        conservative = entry
        if ote is not None and ote > entry:
            conservative = ote
        elif zone is not None and zone.high is not None:
            conservative = float(zone.high)
        elif zone is not None:
            conservative = float(zone.price)
        elif atr > 0:
            conservative = entry + atr * 0.4

        # For sells: aggressive (near market) <= optimal <= conservative (higher)
        levels = sorted([aggressive, optimal_low, optimal_high, conservative])
        aggressive, optimal_low, optimal_high, conservative = levels

        if optimal_low > entry:
            optimal_low = min(entry, optimal_high)
        if optimal_high < entry:
            optimal_high = max(entry, optimal_low)

        return EntryZone(
            aggressive=round_price(aggressive, digits),
            optimal_low=round_price(optimal_low, digits),
            optimal_high=round_price(optimal_high, digits),
            conservative=round_price(conservative, digits),
        )

    @staticmethod
    def _primary_zone(
        context: StructureContext,
        direction: TradeDirection,
    ) -> ZoneLevel | None:
        if direction == TradeDirection.BUY:
            if context.bullish_order_blocks:
                return context.bullish_order_blocks[-1]
            if context.bullish_fvgs:
                return context.bullish_fvgs[-1]
            return None
        if context.bearish_order_blocks:
            return context.bearish_order_blocks[-1]
        if context.bearish_fvgs:
            return context.bearish_fvgs[-1]
        return None

    @staticmethod
    def _ote_price(context: StructureContext, *, bullish: bool) -> float | None:
        if context.range_high is None or context.range_low is None:
            return None
        span = context.range_high - context.range_low
        if span <= 0:
            return None
        if bullish:
            return context.range_low + span * 0.705
        return context.range_high - span * 0.705

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


entry_zone_service = EntryZoneService()
