"""
Institutional trade validation gates.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logger import logger
from app.core.settings import settings
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import ValidationFlags
from app.risk.symbol_profile import get_symbol_profile


@dataclass(slots=True)
class ValidationResult:
    approved: bool
    flags: ValidationFlags
    reasons: list[str]


class TradeValidator:
    """
    Any critical failure => NO_TRADE.
    """

    def validate(
        self,
        context: StructureContext,
        direction: TradeDirection,
        *,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: float,
        used_structure: str,
        at_liquidity_tp: bool,
    ) -> ValidationResult:
        flags = ValidationFlags()
        reasons: list[str] = []

        want_trend = "BULLISH" if direction == TradeDirection.BUY else "BEARISH"
        flags.trend = context.trend == want_trend
        if not flags.trend:
            reasons.append(f"Trend {context.trend} does not align with {direction.value}.")

        want_smc = "bullish" if direction == TradeDirection.BUY else "bearish"
        flags.bos = (
            context.bos_active
            and str(context.bos_direction or "").lower() == want_smc
        )
        flags.choch = (
            context.choch_active
            and str(context.choch_direction or "").lower() == want_smc
        )

        # Structure confirmation: BOS preferred; CHOCH accepted as alternative MSS.
        structure_confirm = flags.bos or flags.choch
        if settings.REQUIRE_BOS and not structure_confirm:
            reasons.append("BOS/CHOCH not confirmed in trade direction.")
        if settings.REQUIRE_CHOCH and not flags.choch:
            reasons.append("CHOCH not confirmed in trade direction.")

        bos_ok = structure_confirm if settings.REQUIRE_BOS else True
        choch_ok = flags.choch if settings.REQUIRE_CHOCH else True

        min_ratio = float(settings.VOLUME_MIN_RATIO)
        if context.avg_volume <= 0:
            flags.volume = True
        else:
            flags.volume = (context.volume / context.avg_volume) >= min_ratio
        if not flags.volume:
            reasons.append("Volume does not support the move.")

        flags.atr = bool(context.atr_ok and not context.tight_range and context.atr > 0)
        if not flags.atr:
            reasons.append("ATR too low or market ranging tightly.")

        flags.structure_sl = used_structure not in {"none", "atr_fallback", ""}
        # Structure SL preferred; ATR fallback allowed only if structure missing
        # but still must pass min distance / RR. Critical: SL must be behind structure
        # geometrically relative to entry.
        if direction == TradeDirection.BUY:
            geometry_ok = stop_loss < entry < take_profit
            behind = stop_loss < entry
        else:
            geometry_ok = take_profit < entry < stop_loss
            behind = stop_loss > entry

        if not behind or not geometry_ok:
            flags.structure_sl = False
            reasons.append("Stop loss is not behind structure / invalid geometry.")

        flags.liquidity = at_liquidity_tp or risk_reward >= float(settings.MIN_RR)
        if not at_liquidity_tp and risk_reward < float(settings.MIN_RR):
            flags.liquidity = False
            reasons.append("Take profit not at liquidity and RR below minimum.")

        flags.risk_reward = risk_reward >= float(settings.MIN_RR)
        if not flags.risk_reward:
            reasons.append(
                f"Risk reward {risk_reward:.2f} below minimum {settings.MIN_RR}."
            )

        profile = get_symbol_profile(context.symbol, atr=context.atr)
        risk_distance = abs(entry - stop_loss)
        min_distance = max(
            context.atr * float(settings.MIN_SL_ATR_FRACTION),
            profile.min_sl_distance,
        )
        flags.risk_distance = risk_distance >= min_distance * 0.98
        if not flags.risk_distance:
            reasons.append("Risk distance below instrument / ATR minimum.")

        flags.news = not context.news_high_impact
        if not flags.news:
            reasons.append(
                f"Blocked: high-impact news within {settings.NEWS_BLOCK_MINUTES} minutes."
            )

        critical_ok = (
            flags.trend
            and bos_ok
            and choch_ok
            and flags.volume
            and flags.atr
            and behind
            and geometry_ok
            and flags.liquidity
            and flags.risk_reward
            and flags.risk_distance
            and flags.news
        )

        if not critical_ok:
            logger.info(
                "Trade validation failed for %s %s: %s",
                context.symbol,
                direction.value,
                reasons,
            )

        return ValidationResult(
            approved=critical_ok,
            flags=flags,
            reasons=reasons,
        )


trade_validator = TradeValidator()
