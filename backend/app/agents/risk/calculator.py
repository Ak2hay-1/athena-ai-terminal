"""
Risk geometry calculator — ATR SL/TP, RR, position size (evidence only).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd

from app.core.settings import settings
from app.indicators.atr import atr_indicator
from app.risk.symbol_profile import atr_multiplier_for
from app.risk.symbol_profile import distance_to_pips
from app.risk.symbol_profile import get_symbol_profile
from app.trading.calculator import TradingCalculator


def _bias_from_technical(technical: dict[str, Any]) -> str:
    trend = str(technical.get("trend") or "").lower()
    alignment = str(technical.get("ema_alignment") or "").lower()
    if "bull" in trend or alignment == "bullish":
        return "long"
    if "bear" in trend or alignment == "bearish":
        return "short"
    score = float(technical.get("score") or 50)
    if score >= 55:
        return "long"
    if score <= 45:
        return "short"
    return "long"


def calculate_risk_geometry(
    *,
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    technical: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute recommended SL/TP/RR/size from ATR and technical bias.
    """
    if len(candles) < 20:
        return {
            "bias": "long",
            "entry": None,
            "recommended_stop_loss": None,
            "recommended_take_profit": None,
            "risk_reward": 0.0,
            "position_size": 0.0,
            "atr": None,
            "stop_loss_pips": 0.0,
            "max_drawdown_risk_percent": float(settings.MAX_RISK_PERCENT),
            "slippage": int(settings.SLIPPAGE),
            "valid": False,
        }

    df = pd.DataFrame(candles)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    df = atr_indicator.calculate(df)
    last = df.iloc[-1]
    entry = float(last["close"])
    atr = float(last["atr_14"]) if not pd.isna(last.get("atr_14")) else 0.0
    bias = _bias_from_technical(technical)
    mult = atr_multiplier_for(timeframe)
    profile = get_symbol_profile(symbol, atr=atr)

    risk_distance = max(atr * mult, profile.min_sl_distance)
    preferred_rr = float(settings.PREFERRED_RR)

    if bias == "long":
        stop = entry - risk_distance
        take = entry + risk_distance * preferred_rr
    else:
        stop = entry + risk_distance
        take = entry - risk_distance * preferred_rr

    rr = float(
        TradingCalculator.risk_reward_ratio(
            Decimal(str(entry)),
            Decimal(str(stop)),
            Decimal(str(take)),
        )
    )

    sl_pips = distance_to_pips(abs(entry - stop), profile)
    risk_amt = TradingCalculator.risk_amount(
        Decimal(str(settings.RISK_ACCOUNT_BALANCE)),
        Decimal(str(settings.MAX_RISK_PERCENT)),
    )
    # Approx $ per pip per standard lot (majors ~10); metals scaled by pip_size
    pip_value = Decimal("10") if profile.pip_size <= 0.0001 else Decimal("1")
    try:
        lots = TradingCalculator.position_size(
            risk_amt,
            Decimal(str(max(sl_pips, 0.1))),
            pip_value,
            Decimal("0.01"),
            Decimal("10"),
            Decimal("0.01"),
        )
    except ValueError:
        lots = Decimal("0.01")

    atr_series = df["atr_14"].dropna()
    atr_mean = float(atr_series.iloc[-20:].mean()) if len(atr_series) >= 20 else atr
    atr_ratio = (atr / atr_mean) if atr_mean > 0 else 1.0

    return {
        "bias": bias,
        "entry": entry,
        "recommended_stop_loss": round(stop, profile.digits),
        "recommended_take_profit": round(take, profile.digits),
        "risk_reward": rr,
        "position_size": float(lots),
        "atr": atr,
        "atr_ratio": atr_ratio,
        "stop_loss_pips": sl_pips,
        "max_drawdown_risk_percent": float(settings.MAX_RISK_PERCENT),
        "slippage": int(settings.SLIPPAGE),
        "valid": atr > 0 and rr > 0,
    }
