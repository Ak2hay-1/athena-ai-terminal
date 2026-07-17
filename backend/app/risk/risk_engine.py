"""
Institutional Risk Engine orchestrator.

Pipeline:
  trend → structure → liquidity → ATR → invalidation → SL → TP → entry → validate
"""

from __future__ import annotations

import pandas as pd

from app.core.logger import logger
from app.risk.confidence_engine import confidence_engine
from app.risk.entry_service import entry_service
from app.risk.models import EntryType
from app.risk.models import StructureContext
from app.risk.models import TradeDirection
from app.risk.models import TradePlan
from app.risk.models import ValidationFlags
from app.risk.stop_loss_service import stop_loss_service
from app.risk.structure_context import structure_context_builder
from app.risk.symbol_profile import distance_to_pips
from app.risk.symbol_profile import get_symbol_profile
from app.risk.take_profit_service import take_profit_service
from app.risk.trade_validator import trade_validator


class RiskEngine:
    """
    Deterministic trade plan builder.
    """

    def build_plan(
        self,
        dataframe: pd.DataFrame,
        *,
        symbol: str,
        timeframe: str,
        higher_timeframes: dict[str, pd.DataFrame] | None = None,
        news_context: dict | None = None,
        multi_tf_trend: str | None = None,
        context: StructureContext | None = None,
    ) -> TradePlan:
        try:
            ctx = context or structure_context_builder.build(
                dataframe,
                symbol=symbol,
                timeframe=timeframe,
                higher_timeframes=higher_timeframes,
                news_context=news_context,
                multi_tf_trend=multi_tf_trend,
            )
        except Exception as exc:
            logger.exception(exc)
            return TradePlan(
                signal="NO_TRADE",
                trend="SIDEWAYS",
                reasons=[f"Structure context failed: {exc}"],
            )

        direction = self._direction_from_trend(ctx.trend)
        if direction is None:
            return TradePlan(
                signal="NO_TRADE",
                entry=ctx.price,
                entry_type=EntryType.NONE,
                stop_loss=ctx.price,
                take_profit=ctx.price,
                confidence=0,
                trend=ctx.trend,
                sl_reason="No directional trend",
                tp_reason="No trade",
                validation=ValidationFlags(
                    trend=False,
                    atr=ctx.atr_ok and not ctx.tight_range,
                    news=not ctx.news_high_impact,
                ),
                reasons=["Market trend is sideways; no trade."],
            )

        # 1) Invalidation / SL from structure (reference = market; refined after entry)
        provisional_sl = stop_loss_service.calculate(
            ctx,
            direction,
            reference_price=ctx.price,
        )
        if not provisional_sl.valid:
            return TradePlan(
                signal="NO_TRADE",
                entry=ctx.price,
                entry_type=EntryType.NONE,
                stop_loss=ctx.price,
                take_profit=ctx.price,
                confidence=0,
                trend=ctx.trend,
                sl_reason=provisional_sl.sl_reason,
                tp_reason="No trade",
                validation=ValidationFlags(
                    atr=False,
                    news=not ctx.news_high_impact,
                ),
                reasons=[provisional_sl.sl_reason],
            )

        # 2) Entry from structure POIs (limit preferred), constrained by provisional SL
        entry_result = entry_service.calculate(
            ctx,
            direction,
            stop_loss=provisional_sl.stop_loss,
        )

        # 3) Recalculate SL against chosen entry
        sl_result = stop_loss_service.calculate(
            ctx,
            direction,
            reference_price=entry_result.entry,
        )
        if not sl_result.valid:
            return TradePlan(
                signal="NO_TRADE",
                entry=entry_result.entry,
                entry_type=EntryType.NONE,
                stop_loss=entry_result.entry,
                take_profit=entry_result.entry,
                confidence=0,
                trend=ctx.trend,
                sl_reason=sl_result.sl_reason,
                entry_reason=entry_result.entry_reason,
                reasons=[sl_result.sl_reason],
            )

        # 4) Provisional confidence (pre-TP) for dynamic RR
        provisional_confidence = confidence_engine.score(
            ctx,
            direction,
            structure_sl=sl_result.used_structure not in {"none", "atr_fallback"},
        )

        # 5) Take profit at liquidity (or RR fallback)
        tp_result = take_profit_service.calculate(
            ctx,
            direction,
            entry=entry_result.entry,
            stop_loss=sl_result.stop_loss,
            confidence=provisional_confidence,
        )

        confidence = confidence_engine.score(
            ctx,
            direction,
            at_liquidity_tp=tp_result.at_liquidity,
            structure_sl=sl_result.used_structure not in {"none", "atr_fallback"},
            risk_reward=tp_result.risk_reward,
        )

        validation = trade_validator.validate(
            ctx,
            direction,
            entry=entry_result.entry,
            stop_loss=sl_result.stop_loss,
            take_profit=tp_result.take_profit,
            risk_reward=tp_result.risk_reward,
            used_structure=sl_result.used_structure,
            at_liquidity_tp=tp_result.at_liquidity,
        )

        profile = get_symbol_profile(ctx.symbol, atr=ctx.atr)
        risk_pips = distance_to_pips(sl_result.risk_distance, profile)
        reward_pips = distance_to_pips(tp_result.reward_distance, profile)

        if not validation.approved:
            logger.info(
                "NO_TRADE %s %s reasons=%s",
                symbol,
                timeframe,
                validation.reasons,
            )
            return TradePlan(
                signal="NO_TRADE",
                entry=entry_result.entry,
                entry_type=EntryType.NONE,
                stop_loss=sl_result.stop_loss,
                take_profit=tp_result.take_profit,
                risk_pips=risk_pips,
                reward_pips=reward_pips,
                risk_reward=tp_result.risk_reward,
                confidence=confidence,
                sl_reason=sl_result.sl_reason,
                tp_reason=tp_result.tp_reason,
                entry_reason=entry_result.entry_reason,
                trend=ctx.trend,
                validation=validation.flags,
                reasons=validation.reasons or ["Validation failed."],
            )

        return TradePlan(
            signal=direction.value,
            entry=entry_result.entry,
            entry_type=entry_result.entry_type,
            stop_loss=sl_result.stop_loss,
            take_profit=tp_result.take_profit,
            risk_pips=risk_pips,
            reward_pips=reward_pips,
            risk_reward=tp_result.risk_reward,
            confidence=confidence,
            sl_reason=sl_result.sl_reason,
            tp_reason=tp_result.tp_reason,
            entry_reason=entry_result.entry_reason,
            trend=ctx.trend,
            validation=validation.flags,
            reasons=[],
        )

    @staticmethod
    def _direction_from_trend(trend: str) -> TradeDirection | None:
        value = (trend or "").upper()
        if value == "BULLISH":
            return TradeDirection.BUY
        if value == "BEARISH":
            return TradeDirection.SELL
        return None


risk_engine = RiskEngine()
