"""
Qualification Engine — lightweight pre-RiskEngine market filter.

Rejects weak markets before expensive entry/SL/TP/confidence work.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.logger import logger
from app.core.settings import settings
from app.indicators.adx import ADXIndicator
from app.qualification.dynamic_thresholds import resolve_thresholds
from app.qualification.dynamic_thresholds import trading_session
from app.qualification.market_regime import detect_regime
from app.qualification.market_regime import regime_allows_directional_trade
from app.qualification.models import GateCheck
from app.qualification.models import QualificationResult
from app.qualification.mtf_rules import evaluate_mtf_alignment
from app.qualification.mtf_rules import extract_trend_from_frame


class QualificationEngine:
    """Institutional desk pre-filter. No entry/SL/TP/confidence."""

    def evaluate(
        self,
        dataframe: pd.DataFrame,
        *,
        symbol: str,
        timeframe: str,
        analysis: dict[str, Any] | None = None,
        higher_timeframes: dict[str, pd.DataFrame] | None = None,
        multi_tf_summary: dict[str, Any] | None = None,
        news_context: dict[str, Any] | None = None,
        spread: float | None = None,
        historical_win_rate: float | None = None,
    ) -> QualificationResult:
        analysis = analysis or {}
        news = news_context or {}
        gates: list[GateCheck] = []
        reasons: list[str] = []

        if dataframe is None or dataframe.empty:
            return QualificationResult(
                qualified=False,
                reasons=["No candle data available."],
                quality_score=0,
                gates=[
                    GateCheck(name="Data Availability", passed=False, detail="Empty frame"),
                ],
            )

        df = self._ensure_indicators(dataframe)
        session = trading_session()
        trend = extract_trend_from_frame(df)
        if isinstance(analysis.get("trend"), dict):
            trend = str(analysis["trend"].get("direction") or trend).upper()

        atr = float(df["atr_14"].iloc[-1] or 0.0) if "atr_14" in df.columns else 0.0
        price = float(df["close"].iloc[-1] or 0.0)
        adx_raw = float(df["adx_14"].iloc[-1] or 0.0) if "adx_14" in df.columns else 0.0
        adx = 0.0 if adx_raw != adx_raw else adx_raw  # NaN → 0
        atr = 0.0 if atr != atr else atr

        bos_active = bool((analysis.get("market_structure") or {}).get("bos")) or bool(
            analysis.get("bos")
        )
        choch_active = bool((analysis.get("market_structure") or {}).get("choch")) or bool(
            analysis.get("choch")
        )
        if "bos" in df.columns:
            bos_active = bos_active or bool(df["bos"].tail(12).fillna(False).any())
        if "choch" in df.columns:
            choch_active = choch_active or bool(df["choch"].tail(12).fillna(False).any())

        regime = detect_regime(
            df,
            analysis=analysis,
            trend=trend,
            atr=atr,
            bos_active=bos_active,
            choch_active=choch_active,
        )
        thresholds = resolve_thresholds(
            regime=regime,
            session=session,
            historical_win_rate=historical_win_rate,
        )

        # --- Gate: Regime allows directional trade ---
        regime_ok = regime_allows_directional_trade(regime)
        gates.append(
            GateCheck(
                name="Market Regime",
                passed=regime_ok,
                detail=regime,
            )
        )
        if not regime_ok:
            reasons.append(f"Regime {regime} is not tradeable (stand aside).")

        # --- Gate: Trend strength (ADX) ---
        min_adx = float(thresholds["min_adx"])
        trend_ok = trend in {"BULLISH", "BEARISH"} and adx >= min_adx
        gates.append(
            GateCheck(
                name="Trend Strength",
                passed=trend_ok,
                detail=f"trend={trend}, ADX={adx:.1f}, min={min_adx:.1f}",
            )
        )
        if not trend_ok:
            reasons.append(
                f"Trend weak (trend={trend}, ADX={adx:.1f} < {min_adx:.1f})."
            )

        # --- Gate: Structure quality ---
        structure_score = self._structure_score(df, analysis, bos_active, choch_active)
        min_structure = float(thresholds["min_structure_score"])
        structure_ok = structure_score >= min_structure
        gates.append(
            GateCheck(
                name="Structure Quality",
                passed=structure_ok,
                detail=f"score={structure_score:.0f}, min={min_structure:.0f}",
            )
        )
        if not structure_ok:
            reasons.append(
                f"Poor structure (score={structure_score:.0f} < {min_structure:.0f})."
            )

        # --- Gate: ATR / volatility ---
        atr_frac = (atr / price) if price > 0 else 0.0
        min_atr = float(thresholds["min_atr_fraction"])
        atr_ok = atr > 0 and atr_frac >= min_atr
        gates.append(
            GateCheck(
                name="ATR / Volatility",
                passed=atr_ok,
                detail=f"atr_frac={atr_frac:.6f}, min={min_atr:.6f}",
            )
        )
        if not atr_ok:
            reasons.append("ATR too low for institutional risk geometry.")

        # --- Gate: Liquidity / volume ---
        vol_ratio = self._volume_ratio(df)
        min_vol = float(thresholds["min_volume_ratio"])
        liquidity_ok = vol_ratio >= min_vol
        gates.append(
            GateCheck(
                name="Liquidity",
                passed=liquidity_ok,
                detail=f"volume_ratio={vol_ratio:.2f}, min={min_vol:.2f}",
            )
        )
        if not liquidity_ok:
            reasons.append(f"Weak liquidity (volume ratio {vol_ratio:.2f}).")

        # --- Gate: Session quality ---
        session_ok = session in set(settings.QUAL_ALLOWED_SESSIONS)
        gates.append(
            GateCheck(
                name="Session Quality",
                passed=session_ok,
                detail=session,
                mandatory=bool(settings.QUAL_ENFORCE_SESSION),
            )
        )
        if settings.QUAL_ENFORCE_SESSION and not session_ok:
            reasons.append(f"Session {session} not allowed for new setups.")

        # --- Gate: Spread ---
        spread_ok = True
        if spread is not None and price > 0:
            max_spread_frac = float(settings.QUAL_MAX_SPREAD_FRACTION)
            spread_frac = float(spread) / price
            spread_ok = spread_frac <= max_spread_frac
            gates.append(
                GateCheck(
                    name="Spread",
                    passed=spread_ok,
                    detail=f"spread_frac={spread_frac:.6f}, max={max_spread_frac:.6f}",
                )
            )
            if not spread_ok:
                reasons.append("Spread too high.")
        else:
            gates.append(
                GateCheck(
                    name="Spread",
                    passed=True,
                    detail="spread unavailable — skipped",
                    mandatory=False,
                )
            )

        # --- Gate: News ---
        news_ok = not bool(news.get("blocked") or news.get("high_impact"))
        gates.append(
            GateCheck(
                name="News Filter",
                passed=news_ok,
                detail="blocked" if not news_ok else "clear",
            )
        )
        if not news_ok:
            reasons.append("High-impact news block active.")

        # --- Gate: HTF alignment ---
        mtf_ok, mtf_gates, mtf_reasons = evaluate_mtf_alignment(
            execution_tf=timeframe,
            execution_trend=trend,
            higher_timeframes=higher_timeframes,
            multi_tf_summary=multi_tf_summary,
        )
        gates.extend(mtf_gates)
        reasons.extend(mtf_reasons)

        mandatory_failed = any(g.mandatory and not g.passed for g in gates)
        # Session is only mandatory when enforced
        if not settings.QUAL_ENFORCE_SESSION:
            mandatory_failed = any(
                g.mandatory and not g.passed and g.name != "Session Quality"
                for g in gates
            )

        quality_score = self._preview_quality_score(
            adx=adx,
            structure_score=structure_score,
            vol_ratio=vol_ratio,
            atr_ok=atr_ok,
            session=session,
            mtf_ok=mtf_ok,
            trend_ok=trend_ok,
        )

        qualified = (
            not mandatory_failed
            and regime_ok
            and trend_ok
            and structure_ok
            and atr_ok
            and liquidity_ok
            and news_ok
            and mtf_ok
            and spread_ok
            and (session_ok or not settings.QUAL_ENFORCE_SESSION)
        )

        if not qualified:
            logger.info(
                "Qualification rejected %s %s regime=%s score=%s reasons=%s",
                symbol,
                timeframe,
                regime,
                quality_score,
                reasons,
            )

        return QualificationResult(
            qualified=qualified,
            reasons=reasons,
            quality_score=quality_score,
            regime=regime,
            gates=gates,
            trend_strength=adx,
            session=session,
            thresholds=thresholds,
        )

    def _ensure_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        df = dataframe
        needs_adx = "adx_14" not in df.columns
        needs_atr = "atr_14" not in df.columns
        if not needs_adx and not needs_atr:
            return df
        try:
            if needs_atr:
                from app.indicators.indicator_engine import indicator_engine

                df = indicator_engine.calculate(df)
            if "adx_14" not in df.columns:
                df = ADXIndicator().calculate(df)
        except Exception as exc:
            logger.warning("Qualification indicator calc skipped: %s", exc)
        return df

    @staticmethod
    def _volume_ratio(df: pd.DataFrame) -> float:
        col = "tick_volume" if "tick_volume" in df.columns else (
            "volume" if "volume" in df.columns else None
        )
        if col is None:
            return 1.0
        lookback = int(settings.VOLUME_AVG_LOOKBACK)
        series = df[col].astype(float).tail(lookback)
        if series.empty:
            return 1.0
        avg = float(series.mean())
        latest = float(series.iloc[-1])
        if avg <= 0:
            return 1.0
        return latest / avg

    @staticmethod
    def _structure_score(
        df: pd.DataFrame,
        analysis: dict[str, Any],
        bos_active: bool,
        choch_active: bool,
    ) -> float:
        score = 0.0
        if bos_active:
            score += 40.0
        if choch_active:
            score += 25.0
        confluence = analysis.get("confluence") or {}
        if isinstance(confluence, dict):
            score += min(35.0, float(confluence.get("score") or 0) * 0.35)
        # Pattern columns boost
        for col, pts in (("order_block", 10.0), ("fvg", 10.0), ("liquidity_sweep", 10.0)):
            if col in df.columns and bool(df[col].tail(20).fillna(False).any()):
                score += pts
        return min(100.0, score)

    @staticmethod
    def _preview_quality_score(
        *,
        adx: float,
        structure_score: float,
        vol_ratio: float,
        atr_ok: bool,
        session: str,
        mtf_ok: bool,
        trend_ok: bool,
    ) -> int:
        """Fast approximate quality (0–100) for early filtering / logging."""
        trend_pts = min(20.0, (adx / 50.0) * 20.0) if trend_ok else 0.0
        structure_pts = min(20.0, structure_score * 0.20)
        liquidity_pts = min(15.0, max(0.0, (vol_ratio - 0.5) / 1.5) * 15.0)
        momentum_pts = min(15.0, (adx / 40.0) * 15.0) if trend_ok else 0.0
        rr_pts = 10.0  # unknown pre-risk; neutral mid
        vol_pts = 10.0 if atr_ok else 0.0
        session_pts = 5.0 if session in {"London", "New York", "Overlap"} else 2.0
        mtf_pts = 5.0 if mtf_ok else 0.0
        total = (
            trend_pts
            + structure_pts
            + liquidity_pts
            + momentum_pts
            + rr_pts
            + vol_pts
            + session_pts
            + mtf_pts
        )
        return int(round(min(100.0, max(0.0, total))))


qualification_engine = QualificationEngine()
