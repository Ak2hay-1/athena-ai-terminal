"""
Legacy risk engine wrapper.

Deprecated: use ``app.risk.risk_engine`` for institutional SL/TP.
Kept for backward-compatible imports and simple ATR helpers in tests.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from app.core.settings import settings
from app.risk.symbol_profile import atr_multiplier_for
from app.risk.symbol_profile import get_symbol_profile
from app.risk.symbol_profile import round_price


@dataclass(slots=True)
class TradeLevels:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float


class RiskEngine:
    """
    Deprecated ATR-only helper. Prefer ``app.risk.RiskEngine.build_plan``.
    """

    ATR_MULTIPLIER = 1.5
    DEFAULT_RR = 2.0

    def calculate(
        self,
        direction: str,
        entry: float,
        atr: float,
        rr: float | None = None,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> TradeLevels:
        warnings.warn(
            "app.analysis.risk_engine is deprecated; use app.risk.risk_engine",
            DeprecationWarning,
            stacklevel=2,
        )

        rr = float(rr if rr is not None else settings.RISK_REWARD_RATIO)
        profile = get_symbol_profile(symbol or "", atr=float(atr or 0))
        mult = (
            atr_multiplier_for(timeframe or "M5")
            if timeframe
            else float(settings.ATR_MULTIPLIER)
        )
        risk = max(float(atr or 0) * mult, profile.min_sl_distance, profile.pip_size)
        direction = (direction or "").upper()
        entry = float(entry)

        if direction == "BUY":
            stop_loss = entry - risk
            take_profit = entry + (risk * rr)
        elif direction == "SELL":
            stop_loss = entry + risk
            take_profit = entry - (risk * rr)
        else:
            rounded = round_price(entry, profile.digits)
            return TradeLevels(
                entry=rounded,
                stop_loss=rounded,
                take_profit=rounded,
                risk_reward=0.0,
            )

        return TradeLevels(
            entry=round_price(entry, profile.digits),
            stop_loss=round_price(stop_loss, profile.digits),
            take_profit=round_price(take_profit, profile.digits),
            risk_reward=round(rr, 2),
        )


risk_engine = RiskEngine()
