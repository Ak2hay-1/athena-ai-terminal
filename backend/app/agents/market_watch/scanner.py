"""
Market Watch scanner — detect meaningful market changes (no AI).
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from typing import Any

import pandas as pd

from app.core.constants import SUPPORTED_SYMBOLS
from app.core.constants import SUPPORTED_TIMEFRAMES
from app.core.logger import get_logger
from app.core.settings import settings
from app.indicators.atr import atr_indicator
from app.indicators.bollinger import bollinger_indicator
from app.indicators.moving_average import moving_average_indicator
from app.indicators.volume_ma import volume_ma_indicator
from app.patterns.swing_detector import swing_detector

logger = get_logger("athena.agents.market_watch")

# UTC hour windows (approx) for major FX sessions
_SESSION_WINDOWS: dict[str, tuple[int, int]] = {
    "asia": (0, 9),
    "london": (7, 16),
    "new_york": (12, 21),
}


@dataclass
class PairState:
    last_candle_time: str | None = None
    trend_alignment: str | None = None
    active_sessions: set[str] = field(default_factory=set)
    support: float | None = None
    resistance: float | None = None


def candles_to_dataframe(candles: list[dict[str, Any]]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame(
            columns=["time", "open", "high", "low", "close", "tick_volume"]
        )
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    for col in ("open", "high", "low", "close", "tick_volume"):
        df[col] = df[col].astype(float)
    return df.sort_values("time").reset_index(drop=True)


def _ema_alignment(row: pd.Series) -> str:
    e9 = row.get("ema_9")
    e20 = row.get("ema_20")
    e50 = row.get("ema_50")
    if pd.isna(e9) or pd.isna(e20) or pd.isna(e50):
        return "neutral"
    if e9 > e20 > e50:
        return "bullish"
    if e9 < e20 < e50:
        return "bearish"
    return "neutral"


def _active_sessions(now: datetime) -> set[str]:
    hour = now.astimezone(timezone.utc).hour
    active: set[str] = set()
    for name, (start, end) in _SESSION_WINDOWS.items():
        if start <= hour < end:
            active.add(name)
    return active


def _change(
    *,
    symbol: str,
    timeframe: str,
    change_type: str,
    price: float,
    timestamp: str,
    market_state: dict[str, Any],
    previous_state: dict[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "change_type": change_type,
        "price": price,
        "timestamp": timestamp,
        "market_state": market_state,
        "previous_state": previous_state,
        **extra,
    }


def detect_changes(
    *,
    symbol: str,
    timeframe: str,
    candles: list[dict[str, Any]],
    state: PairState,
) -> list[dict[str, Any]]:
    """
    Detect meaningful changes for one symbol/timeframe pair.
    """
    df = candles_to_dataframe(candles)
    if len(df) < 30:
        return []

    df = moving_average_indicator.calculate(df)
    df = atr_indicator.calculate(df)
    df = bollinger_indicator.calculate(df)
    df = volume_ma_indicator.calculate(df)
    df = swing_detector.detect(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]
    candle_time = last["time"]
    if hasattr(candle_time, "isoformat"):
        candle_time_str = candle_time.isoformat()
    else:
        candle_time_str = str(candle_time)

    price = float(last["close"])
    atr = float(last["atr_14"]) if not pd.isna(last.get("atr_14")) else None
    alignment = _ema_alignment(last)

    # Support / resistance from recent swings
    recent = df.tail(80)
    swing_highs = recent.loc[recent["swing_high"], "high"]
    swing_lows = recent.loc[recent["swing_low"], "low"]
    resistance = float(swing_highs.iloc[-1]) if len(swing_highs) else None
    support = float(swing_lows.iloc[-1]) if len(swing_lows) else None

    now = datetime.now(timezone.utc)
    sessions = _active_sessions(now)

    market_state = {
        "price": price,
        "trend_alignment": alignment,
        "atr": atr,
        "support": support,
        "resistance": resistance,
        "sessions": sorted(sessions),
        "volume_ratio": (
            float(last["volume_ratio"])
            if not pd.isna(last.get("volume_ratio"))
            else None
        ),
        "bb_width": (
            float(last["bb_width"]) if not pd.isna(last.get("bb_width")) else None
        ),
    }
    previous_state = {
        "last_candle_time": state.last_candle_time,
        "trend_alignment": state.trend_alignment,
        "support": state.support,
        "resistance": state.resistance,
        "sessions": sorted(state.active_sessions),
    }

    changes: list[dict[str, Any]] = []

    # New candle
    if state.last_candle_time != candle_time_str:
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="new_candle",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
            )
        )

    # Volume spike
    vol_ratio = market_state["volume_ratio"]
    if (
        vol_ratio is not None
        and vol_ratio >= settings.MARKET_WATCH_VOLUME_SPIKE_RATIO
    ):
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="volume_spike",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                volume_ratio=vol_ratio,
            )
        )

    # ATR expansion
    atr_series = df["atr_14"].dropna()
    if len(atr_series) >= 20 and atr is not None:
        atr_mean = float(atr_series.iloc[-20:].mean())
        if atr_mean > 0 and atr / atr_mean >= settings.MARKET_WATCH_ATR_EXPANSION_RATIO:
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="atr_expansion",
                    price=price,
                    timestamp=candle_time_str,
                    market_state=market_state,
                    previous_state=previous_state,
                    atr_ratio=atr / atr_mean,
                )
            )

    # Volatility spike via BB width
    bb_width = market_state["bb_width"]
    bb_series = df["bb_width"].dropna()
    if bb_width is not None and len(bb_series) >= 20:
        bb_mean = float(bb_series.iloc[-20:].mean())
        if bb_mean > 0 and bb_width / bb_mean >= settings.MARKET_WATCH_ATR_EXPANSION_RATIO:
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="volatility_spike",
                    price=price,
                    timestamp=candle_time_str,
                    market_state=market_state,
                    previous_state=previous_state,
                    bb_width_ratio=bb_width / bb_mean,
                )
            )

    # Swing high / low on previous confirmed bar (lookback leaves last bars unmarked)
    lookback = swing_detector.lookback
    if len(df) > lookback * 2 + 1:
        confirmed = df.iloc[-(lookback + 1)]
        confirmed_time = confirmed["time"]
        confirmed_ts = (
            confirmed_time.isoformat()
            if hasattr(confirmed_time, "isoformat")
            else str(confirmed_time)
        )
        if bool(confirmed.get("swing_high")):
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="swing_high",
                    price=float(confirmed["high"]),
                    timestamp=confirmed_ts,
                    market_state=market_state,
                    previous_state=previous_state,
                )
            )
        if bool(confirmed.get("swing_low")):
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="swing_low",
                    price=float(confirmed["low"]),
                    timestamp=confirmed_ts,
                    market_state=market_state,
                    previous_state=previous_state,
                )
            )

    # Breakout / breakdown vs prior support/resistance
    if state.resistance is not None and price > state.resistance:
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="breakout",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                level=state.resistance,
            )
        )
    if state.support is not None and price < state.support:
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="breakdown",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                level=state.support,
            )
        )

    # Trend changed
    if (
        state.trend_alignment
        and alignment != "neutral"
        and state.trend_alignment != alignment
    ):
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="trend_changed",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                from_trend=state.trend_alignment,
                to_trend=alignment,
            )
        )

    # Session open / close
    opened = sessions - state.active_sessions
    closed = state.active_sessions - sessions
    for session_name in opened:
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="session_open",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                session=session_name,
            )
        )
    for session_name in closed:
        changes.append(
            _change(
                symbol=symbol,
                timeframe=timeframe,
                change_type="session_close",
                price=price,
                timestamp=candle_time_str,
                market_state=market_state,
                previous_state=previous_state,
                session=session_name,
            )
        )

    # Gap detected
    if atr is not None and atr > 0:
        gap = abs(float(last["open"]) - float(prev["close"]))
        if gap >= settings.MARKET_WATCH_GAP_ATR_FRACTION * atr:
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="gap_detected",
                    price=price,
                    timestamp=candle_time_str,
                    market_state=market_state,
                    previous_state=previous_state,
                    gap_size=gap,
                )
            )

    # Level cross (prior stored levels)
    if state.support is not None:
        prev_close = float(prev["close"])
        if (prev_close - state.support) * (price - state.support) < 0:
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="level_cross",
                    price=price,
                    timestamp=candle_time_str,
                    market_state=market_state,
                    previous_state=previous_state,
                    level=state.support,
                    level_kind="support",
                )
            )
    if state.resistance is not None:
        prev_close = float(prev["close"])
        if (prev_close - state.resistance) * (price - state.resistance) < 0:
            changes.append(
                _change(
                    symbol=symbol,
                    timeframe=timeframe,
                    change_type="level_cross",
                    price=price,
                    timestamp=candle_time_str,
                    market_state=market_state,
                    previous_state=previous_state,
                    level=state.resistance,
                    level_kind="resistance",
                )
            )

    # Update state for caller
    state.last_candle_time = candle_time_str
    state.trend_alignment = alignment
    state.active_sessions = sessions
    state.support = support
    state.resistance = resistance

    return changes


def normalize_watch_universe() -> tuple[list[str], list[str]]:
    symbols = [
        s.upper().strip()
        for s in settings.MARKET_WATCH_SYMBOLS
        if s.upper().strip() in SUPPORTED_SYMBOLS
    ]
    timeframes = [
        t.upper().strip()
        for t in settings.MARKET_WATCH_TIMEFRAMES
        if t.upper().strip() in SUPPORTED_TIMEFRAMES
    ]
    skipped_symbols = [
        s for s in settings.MARKET_WATCH_SYMBOLS if s.upper().strip() not in SUPPORTED_SYMBOLS
    ]
    skipped_tfs = [
        t
        for t in settings.MARKET_WATCH_TIMEFRAMES
        if t.upper().strip() not in SUPPORTED_TIMEFRAMES
    ]
    if skipped_symbols:
        logger.warning(
            "market_watch action=config skipped_symbols=%s",
            skipped_symbols,
        )
    if skipped_tfs:
        logger.warning(
            "market_watch action=config skipped_timeframes=%s",
            skipped_tfs,
        )
    return symbols, timeframes
