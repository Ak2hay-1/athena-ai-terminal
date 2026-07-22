"""
Institutional trade validation gates.

Any critical failure => NO_TRADE (never soft-downgrade confidence).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logger import logger
from app.core.settings import settings
from app.qualification.market_regime import regime_allows_directional_trade
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
    Critical failures immediately reject the trade.
    Do NOT reduce confidence — return NO_TRADE upstream.
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
        spread: float | None = None,
        market_regime: str | None = None,
        mtf_aligned: bool | None = None,
        trend_strength: float | None = None,
    ) -> ValidationResult:
        flags = ValidationFlags()
        reasons: list[str] = []

        want_trend = "BULLISH" if direction == TradeDirection.BUY else "BEARISH"
        flags.trend = context.trend == want_trend
        if not flags.trend:
            reasons.append(f"Trend {context.trend} does not align with {direction.value}.")

        # Weak trend (ADX) is a hard reject when provided
        min_adx = float(settings.QUAL_MIN_ADX)
        if trend_strength is not None and float(trend_strength) < min_adx:
            flags.trend = False
            reasons.append(
                f"Trend weak (ADX={float(trend_strength):.1f} < {min_adx:.1f})."
            )

        want_smc = "bullish" if direction == TradeDirection.BUY else "bearish"
        flags.bos = (
            context.bos_active
            and str(context.bos_direction or "").lower() == want_smc
        )
        flags.choch = (
            context.choch_active
            and str(context.choch_direction or "").lower() == want_smc
        )

        structure_confirm = flags.bos or flags.choch
        if settings.REQUIRE_BOS and not structure_confirm:
            reasons.append("BOS/CHOCH not confirmed in trade direction.")
        if settings.REQUIRE_CHOCH and not flags.choch:
            reasons.append("CHOCH not confirmed in trade direction.")

        bos_ok = structure_confirm if settings.REQUIRE_BOS else True
        choch_ok = flags.choch if settings.REQUIRE_CHOCH else True

        # Poor structure (no BOS/CHOCH when required) already gated; also reject
        # ATR-only SL as poor structure when REQUIRE_BOS is on.
        poor_structure = used_structure in {"none", "atr_fallback", ""}
        if settings.REQUIRE_BOS and poor_structure and not structure_confirm:
            reasons.append("Poor structure — no valid structural invalidation.")

        min_ratio = float(settings.VOLUME_MIN_RATIO)
        if context.avg_volume <= 0:
            flags.volume = True
        else:
            flags.volume = (context.volume / context.avg_volume) >= min_ratio
        if not flags.volume:
            reasons.append("Poor liquidity — volume does not support the move.")

        flags.atr = bool(context.atr_ok and not context.tight_range and context.atr > 0)
        if not flags.atr:
            reasons.append("ATR below threshold or market ranging tightly.")

        flags.structure_sl = used_structure not in {"none", "atr_fallback", ""}
        if direction == TradeDirection.BUY:
            geometry_ok = stop_loss < entry < take_profit
            behind = stop_loss < entry
        else:
            geometry_ok = take_profit < entry < stop_loss
            behind = stop_loss > entry

        if not behind or not geometry_ok:
            flags.structure_sl = False
            reasons.append("Invalid SL — not behind structure / invalid geometry.")

        flags.liquidity = at_liquidity_tp or risk_reward >= float(settings.MIN_RR)
        if not at_liquidity_tp and risk_reward < float(settings.MIN_RR):
            flags.liquidity = False
            reasons.append("Poor liquidity at TP and RR below minimum.")

        flags.risk_reward = risk_reward >= float(settings.MIN_RR)
        if not flags.risk_reward:
            reasons.append(
                f"RR below minimum ({risk_reward:.2f} < {settings.MIN_RR})."
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

        # Spread hard gate
        flags.spread = True
        if spread is not None and context.price > 0:
            max_frac = float(settings.QUAL_MAX_SPREAD_FRACTION)
            spread_frac = float(spread) / float(context.price)
            flags.spread = spread_frac <= max_frac
            if not flags.spread:
                reasons.append(
                    f"Spread too high ({spread_frac:.6f} > {max_frac:.6f})."
                )

        # Regime hard gate
        flags.regime = True
        if market_regime:
            flags.regime = regime_allows_directional_trade(market_regime)
            if not flags.regime:
                reasons.append(f"Regime {market_regime} incompatible with directional trade.")

        # MTF hard gate (when caller supplies alignment result)
        flags.mtf = True if mtf_aligned is None else bool(mtf_aligned)
        if mtf_aligned is False:
            reasons.append("Higher timeframe disagreement.")

        structure_ok = (not poor_structure) or (not settings.REQUIRE_BOS) or structure_confirm

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
            and flags.spread
            and flags.regime
            and flags.mtf
            and structure_ok
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
