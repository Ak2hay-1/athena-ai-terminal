"""
Build StructureContext from patterned OHLCV frames.
"""

from __future__ import annotations

import pandas as pd

from app.core.logger import logger
from app.core.settings import settings
from app.indicators.indicator_engine import indicator_engine
from app.patterns.pattern_engine import pattern_engine
from app.risk.models import StructureContext
from app.risk.models import ZoneLevel


class StructureContextBuilder:
    """
    Extract swings, OBs, FVGs, liquidity and HTF targets.
    """

    def build(
        self,
        dataframe: pd.DataFrame,
        *,
        symbol: str,
        timeframe: str,
        higher_timeframes: dict[str, pd.DataFrame] | None = None,
        news_context: dict | None = None,
        multi_tf_trend: str | None = None,
    ) -> StructureContext:
        if dataframe.empty:
            raise ValueError("Cannot build structure context from empty dataframe.")

        df = dataframe.copy()
        if "atr_14" not in df.columns:
            df = indicator_engine.calculate(df)
        if "swing_high" not in df.columns:
            df = pattern_engine.detect(df)

        lookback = int(settings.STRUCTURE_LOOKBACK_BARS)
        window = df.tail(max(lookback, 30)).copy()
        latest = window.iloc[-1]
        price = float(latest["close"])
        atr = float(latest.get("atr_14") or 0.0)

        vol_lookback = int(settings.VOLUME_AVG_LOOKBACK)
        volumes = window["tick_volume"].astype(float).tail(vol_lookback)
        avg_volume = float(volumes.mean()) if len(volumes) else 0.0
        volume = float(latest.get("tick_volume") or 0.0)

        swing_highs = self._collect_swing_prices(window, "swing_high", "high")
        swing_lows = self._collect_swing_prices(window, "swing_low", "low")

        bullish_obs, bearish_obs = self._collect_order_blocks(window, price)
        bullish_fvgs, bearish_fvgs = self._collect_fvgs(window, price)
        equal_highs, equal_lows = self._collect_equal_levels(window)
        sweep_highs, sweep_lows = self._detect_sweeps(window, swing_highs, swing_lows)

        liq_high, liq_low = self._build_liquidity_targets(
            price=price,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            equal_highs=equal_highs,
            equal_lows=equal_lows,
            bearish_obs=bearish_obs,
            bullish_obs=bullish_obs,
            higher_timeframes=higher_timeframes,
        )

        atr_frac = (atr / price) if price > 0 else 0.0
        atr_ok = atr > 0 and atr_frac >= float(settings.ATR_MIN_FRACTION_OF_PRICE)

        range_high = float(latest["range_high"]) if pd.notna(latest.get("range_high")) else None
        range_low = float(latest["range_low"]) if pd.notna(latest.get("range_low")) else None
        tight_range = False
        if range_high is not None and range_low is not None and atr > 0:
            tight_range = (range_high - range_low) < (atr * 1.2)

        bos_active, bos_direction = self._recent_event(
            window,
            flag_col="bos",
            direction_col="bos_direction",
            bars=12,
        )
        choch_active, choch_direction = self._recent_event(
            window,
            flag_col="choch",
            direction_col="choch_direction",
            bars=12,
        )

        news = news_context or {}
        ctx = StructureContext(
            symbol=symbol.upper(),
            timeframe=timeframe.upper(),
            price=price,
            atr=atr,
            trend=str(latest.get("trend") or "SIDEWAYS"),
            volume=volume,
            avg_volume=avg_volume,
            bos_active=bos_active,
            bos_direction=bos_direction,
            choch_active=choch_active,
            choch_direction=choch_direction,
            in_premium=bool(latest.get("premium")),
            in_discount=bool(latest.get("discount")),
            equilibrium=(
                float(latest["equilibrium"])
                if pd.notna(latest.get("equilibrium"))
                else None
            ),
            range_high=range_high,
            range_low=range_low,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            bullish_order_blocks=bullish_obs,
            bearish_order_blocks=bearish_obs,
            bullish_fvgs=bullish_fvgs,
            bearish_fvgs=bearish_fvgs,
            equal_highs=equal_highs,
            equal_lows=equal_lows,
            liquidity_sweep_highs=sweep_highs,
            liquidity_sweep_lows=sweep_lows,
            liquidity_targets_high=liq_high,
            liquidity_targets_low=liq_low,
            multi_tf_trend=multi_tf_trend,
            news_high_impact=bool(news.get("high_impact_upcoming")),
            news_sentiment=(
                float(news["sentiment_score"])
                if news.get("sentiment_score") is not None
                else None
            ),
            atr_ok=atr_ok,
            tight_range=tight_range,
        )
        logger.debug(
            "StructureContext %s %s trend=%s atr=%.5f swings=%d/%d",
            symbol,
            timeframe,
            ctx.trend,
            atr,
            len(swing_highs),
            len(swing_lows),
        )
        return ctx

    @staticmethod
    def _recent_event(
        window: pd.DataFrame,
        *,
        flag_col: str,
        direction_col: str,
        bars: int,
    ) -> tuple[bool, str | None]:
        if flag_col not in window.columns:
            return False, None
        recent = window.tail(bars)
        hits = recent[recent[flag_col] == True]  # noqa: E712
        if hits.empty:
            return False, None
        last = hits.iloc[-1]
        direction = last.get(direction_col)
        return True, (str(direction) if direction is not None else None)

    @staticmethod
    def _collect_swing_prices(
        window: pd.DataFrame,
        flag_col: str,
        price_col: str,
    ) -> list[float]:
        if flag_col not in window.columns:
            return []
        rows = window[window[flag_col] == True]  # noqa: E712
        prices = [float(v) for v in rows[price_col].tolist() if pd.notna(v)]
        return prices[-8:]

    @staticmethod
    def _collect_order_blocks(
        window: pd.DataFrame,
        price: float,
    ) -> tuple[list[ZoneLevel], list[ZoneLevel]]:
        bullish: list[ZoneLevel] = []
        bearish: list[ZoneLevel] = []
        if "order_block" not in window.columns:
            return bullish, bearish

        for _, row in window[window["order_block"] == True].iterrows():  # noqa: E712
            high = float(row.get("ob_high") or row["high"])
            low = float(row.get("ob_low") or row["low"])
            direction = str(row.get("ob_direction") or "").lower()
            zone = ZoneLevel(
                price=(high + low) / 2.0,
                kind="order_block",
                high=high,
                low=low,
                direction=direction or None,
            )
            if direction == "bullish" or (not direction and low <= price):
                # Unmitigated-ish: still below/near price for demand
                if high >= price * 0.995:
                    bullish.append(zone)
            if direction == "bearish" or (not direction and high >= price):
                if low <= price * 1.005:
                    bearish.append(zone)

        return bullish[-6:], bearish[-6:]

    @staticmethod
    def _collect_fvgs(
        window: pd.DataFrame,
        price: float,
    ) -> tuple[list[ZoneLevel], list[ZoneLevel]]:
        bullish: list[ZoneLevel] = []
        bearish: list[ZoneLevel] = []
        if "fvg" not in window.columns:
            return bullish, bearish

        for _, row in window[window["fvg"] == True].iterrows():  # noqa: E712
            upper = float(row.get("fvg_upper") or row["high"])
            lower = float(row.get("fvg_lower") or row["low"])
            direction = str(row.get("fvg_direction") or "").lower()
            zone = ZoneLevel(
                price=(upper + lower) / 2.0,
                kind="fvg",
                high=upper,
                low=lower,
                direction=direction or None,
            )
            # Unfilled: price still outside or inside gap
            if direction == "bullish" and price >= lower:
                bullish.append(zone)
            elif direction == "bearish" and price <= upper:
                bearish.append(zone)
            elif not direction:
                if lower < price:
                    bullish.append(zone)
                else:
                    bearish.append(zone)

        return bullish[-6:], bearish[-6:]

    @staticmethod
    def _collect_equal_levels(
        window: pd.DataFrame,
    ) -> tuple[list[float], list[float]]:
        highs: list[float] = []
        lows: list[float] = []
        if "equal_high" in window.columns:
            for _, row in window[window["equal_high"] == True].iterrows():  # noqa: E712
                highs.append(float(row["high"]))
        if "equal_low" in window.columns:
            for _, row in window[window["equal_low"] == True].iterrows():  # noqa: E712
                lows.append(float(row["low"]))
        return highs[-6:], lows[-6:]

    @staticmethod
    def _detect_sweeps(
        window: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
    ) -> tuple[list[float], list[float]]:
        """Wick beyond prior swing / equal level with close back inside."""
        sweep_highs: list[float] = []
        sweep_lows: list[float] = []
        if len(window) < 3:
            return sweep_highs, sweep_lows

        ref_highs = swing_highs[:-1] if len(swing_highs) > 1 else swing_highs
        ref_lows = swing_lows[:-1] if len(swing_lows) > 1 else swing_lows

        for i in range(1, len(window)):
            row = window.iloc[i]
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            for level in ref_highs[-4:]:
                if high > level and close < level:
                    sweep_highs.append(level)
            for level in ref_lows[-4:]:
                if low < level and close > level:
                    sweep_lows.append(level)

        # unique preserve order
        def _uniq(values: list[float]) -> list[float]:
            seen: set[float] = set()
            out: list[float] = []
            for v in values:
                key = round(v, 8)
                if key in seen:
                    continue
                seen.add(key)
                out.append(v)
            return out[-6:]

        return _uniq(sweep_highs), _uniq(sweep_lows)

    def _build_liquidity_targets(
        self,
        *,
        price: float,
        swing_highs: list[float],
        swing_lows: list[float],
        equal_highs: list[float],
        equal_lows: list[float],
        bearish_obs: list[ZoneLevel],
        bullish_obs: list[ZoneLevel],
        higher_timeframes: dict[str, pd.DataFrame] | None,
    ) -> tuple[list[ZoneLevel], list[ZoneLevel]]:
        highs: list[ZoneLevel] = []
        lows: list[ZoneLevel] = []

        for level in equal_highs:
            if level > price:
                highs.append(ZoneLevel(price=level, kind="equal_high"))
        for level in equal_lows:
            if level < price:
                lows.append(ZoneLevel(price=level, kind="equal_low"))

        for level in swing_highs:
            if level > price:
                highs.append(ZoneLevel(price=level, kind="previous_high"))
        for level in swing_lows:
            if level < price:
                lows.append(ZoneLevel(price=level, kind="previous_low"))

        for ob in bearish_obs:
            level = float(ob.low if ob.low is not None else ob.price)
            if level > price:
                highs.append(ZoneLevel(price=level, kind="opposite_order_block", high=ob.high, low=ob.low))
        for ob in bullish_obs:
            level = float(ob.high if ob.high is not None else ob.price)
            if level < price:
                lows.append(ZoneLevel(price=level, kind="opposite_order_block", high=ob.high, low=ob.low))

        htf_highs, htf_lows = self._htf_liquidity(higher_timeframes)
        for kind, level in htf_highs:
            if level > price:
                highs.append(ZoneLevel(price=level, kind=kind))
        for kind, level in htf_lows:
            if level < price:
                lows.append(ZoneLevel(price=level, kind=kind))

        highs.sort(key=lambda z: z.price)
        lows.sort(key=lambda z: z.price, reverse=True)
        return highs, lows

    @staticmethod
    def _htf_liquidity(
        higher_timeframes: dict[str, pd.DataFrame] | None,
    ) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
        highs: list[tuple[str, float]] = []
        lows: list[tuple[str, float]] = []
        if not higher_timeframes:
            return highs, lows

        ranked = sorted(
            higher_timeframes.items(),
            key=lambda item: _tf_rank(item[0]),
            reverse=True,
        )
        for tf, frame in ranked:
            if frame is None or frame.empty:
                continue
            recent = frame.tail(20)
            hi = float(recent["high"].max())
            lo = float(recent["low"].min())
            label_high = "weekly_high" if _tf_rank(tf) >= _tf_rank("H4") else "daily_high"
            label_low = "weekly_low" if _tf_rank(tf) >= _tf_rank("H4") else "daily_low"
            # Prefer prior bar extremes as previous high/low
            if len(recent) >= 2:
                prev = recent.iloc[-2]
                highs.append(("previous_high", float(prev["high"])))
                lows.append(("previous_low", float(prev["low"])))
            highs.append((label_high, hi))
            lows.append((label_low, lo))
        return highs, lows


def _tf_rank(timeframe: str) -> int:
    order = {
        "M1": 1,
        "M5": 2,
        "M15": 3,
        "M30": 4,
        "H1": 5,
        "H4": 6,
        "D1": 7,
        "W1": 8,
    }
    return order.get((timeframe or "").upper(), 0)


structure_context_builder = StructureContextBuilder()
