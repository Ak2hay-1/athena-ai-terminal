"""
Instrument risk profiles and style helpers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import settings


@dataclass(slots=True)
class SymbolProfile:
    symbol: str
    digits: int
    pip_size: float
    tick_size: float
    min_sl_distance: float
    point_size: float | None = None


_SCALP_TFS = {"M1", "M5"}
_INTRADAY_TFS = {"M15", "M30", "H1"}
_SWING_TFS = {"H4", "D1", "W1"}


def trading_style(timeframe: str) -> str:
    tf = (timeframe or "").upper()
    if tf in _SCALP_TFS:
        return "scalp"
    if tf in _SWING_TFS:
        return "swing"
    if tf in _INTRADAY_TFS:
        return "intraday"
    return "intraday"


def atr_multiplier_for(timeframe: str) -> float:
    style = trading_style(timeframe)
    return float(
        settings.ATR_MULTIPLIERS_BY_STYLE.get(
            style,
            settings.ATR_MULTIPLIER,
        )
    )


def _infer_defaults(symbol: str) -> dict:
    name = symbol.upper().replace("/", "").replace(".", "")
    if "JPY" in name:
        return {
            "digits": 3,
            "pip_size": 0.01,
            "min_sl_pips": 10,
            "tick_size": 0.001,
        }
    if name.startswith("XAU"):
        return {
            "digits": 2,
            "pip_size": 0.1,
            "point_size": 0.01,
            "min_sl_points": 150,
            "tick_size": 0.01,
        }
    return {
        "digits": 5,
        "pip_size": 0.0001,
        "min_sl_pips": 8,
        "tick_size": 0.00001,
    }


def get_symbol_profile(symbol: str, atr: float = 0.0) -> SymbolProfile:
    name = (symbol or "").upper().replace("/", "").replace(".", "")
    raw = dict(settings.INSTRUMENT_RISK_PROFILES.get(name) or _infer_defaults(name))

    digits = int(raw.get("digits", 5))
    pip_size = float(raw.get("pip_size", 0.0001))
    tick_size = float(raw.get("tick_size", pip_size / 10 if pip_size else 0.00001))
    point_size = raw.get("point_size")
    point_size_f = float(point_size) if point_size is not None else None

    min_distance = 0.0
    if "min_sl_points" in raw and point_size_f:
        min_distance = float(raw["min_sl_points"]) * point_size_f
    elif "min_sl_pips" in raw:
        min_distance = float(raw["min_sl_pips"]) * pip_size
    elif "min_sl_atr_mult" in raw and atr > 0:
        min_distance = float(raw["min_sl_atr_mult"]) * atr
    else:
        min_distance = 8 * pip_size

    return SymbolProfile(
        symbol=name,
        digits=digits,
        pip_size=pip_size,
        tick_size=tick_size,
        min_sl_distance=min_distance,
        point_size=point_size_f,
    )


def round_price(price: float, digits: int) -> float:
    return round(float(price), digits)


def distance_to_pips(distance: float, profile: SymbolProfile) -> float:
    if profile.pip_size <= 0:
        return 0.0
    return round(abs(distance) / profile.pip_size, 2)
