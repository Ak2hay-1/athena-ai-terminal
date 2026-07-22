"""
Scanner service — batch opportunities with server-side ranking.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import SUPPORTED_SYMBOLS
from app.core.constants import SUPPORTED_TIMEFRAMES
from app.core.settings import settings
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.scanner import ScannerGroupCounts
from app.schemas.scanner import ScannerMeta
from app.schemas.scanner import ScannerOpportunitiesResponse
from app.schemas.scanner import ScannerOpportunityRead
from app.schemas.scanner import ScannerScoreBreakdown
from app.services.base_service import BaseService
from app.services.market_service import MarketService
from app.services.scanner_ranker import display_signal
from app.services.scanner_ranker import rank_opportunity
from app.services.scanner_ranker import session_label
from app.services.scanner_ranker import urgency_from_event
from app.services.scanner_state import scanner_state
from app.qualification.correlation_filter import filter_correlated
from app.qualification.recommendation_ranker import rank_opportunities as institutional_rank
from app.qualification.setup_quality import scanner_group_for_score


def _enum_value(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_symbols(raw: list[str] | None) -> list[str]:
    supported = {s.upper() for s in SUPPORTED_SYMBOLS}
    source = raw if raw else list(settings.SCANNER_SYMBOLS)
    out: list[str] = []
    seen: set[str] = set()
    for item in source:
        sym = str(item).upper().strip()
        if not sym or sym in seen:
            continue
        if sym not in supported:
            continue
        seen.add(sym)
        out.append(sym)
    return out


class ScannerService(BaseService):
    """Build ranked scanner board from recommendations + quotes + Market Watch."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.recommendations = RecommendationRepository(db)
        self.watchlist = WatchlistRepository(db)
        self.market = MarketService(db)

    def resolve_universe(
        self,
        *,
        user_id: int | None = None,
        symbols: list[str] | None = None,
        use_watchlist: bool = False,
    ) -> list[str]:
        if symbols:
            return _normalize_symbols(symbols)

        if use_watchlist and user_id is not None:
            entries = self.watchlist.list_for_user(user_id)
            enabled = [
                e.symbol.upper()
                for e in entries
                if getattr(e, "enabled", True)
            ]
            resolved = _normalize_symbols(enabled)
            if resolved:
                return resolved

        return _normalize_symbols(None)

    def get_opportunities(
        self,
        *,
        timeframe: str,
        user_id: int | None = None,
        symbols: list[str] | None = None,
        use_watchlist: bool = False,
        min_score: int | None = None,
        signals: list[str] | None = None,
        actionable_only: bool = False,
        limit: int | None = None,
    ) -> ScannerOpportunitiesResponse:
        tf = timeframe.upper().strip()
        if tf not in SUPPORTED_TIMEFRAMES:
            tf = "M15"

        universe = self.resolve_universe(
            user_id=user_id,
            symbols=symbols,
            use_watchlist=use_watchlist,
        )
        min_score_val = (
            settings.SCANNER_MIN_SCORE_DEFAULT
            if min_score is None
            else max(0, min(100, int(min_score)))
        )
        signal_filter = (
            {s.upper().replace(" ", "_") for s in signals} if signals else None
        )
        now = datetime.now(timezone.utc)
        session = session_label(now)
        stale_minutes = int(settings.SCANNER_STALE_MINUTES)
        strong_threshold = int(settings.SCANNER_STRONG_SIGNAL_CONFIDENCE)
        mw_max_age = int(settings.SCANNER_MARKET_WATCH_MAX_AGE_SECONDS)

        latest = self.recommendations.get_latest_for_symbols(universe, tf)
        quotes = self._quote_map(universe, tf)
        change_map = self._change_percent_map(universe, tf, quotes)
        also_hot = self._also_hot_map(universe, tf)

        opportunities: list[ScannerOpportunityRead] = []
        for symbol in universe:
            rec = latest.get(symbol)
            price = quotes.get(symbol)
            change_pct = change_map.get(symbol)

            if rec is None and price is None:
                continue

            raw_signal = _enum_value(getattr(rec, "signal", None)) or "HOLD"
            confidence = int(getattr(rec, "confidence", 0) or 0)
            display = display_signal(
                raw_signal,
                confidence,
                strong_threshold=strong_threshold,
            )

            mw_event = scanner_state.get_event(
                symbol,
                tf,
                max_age_seconds=mw_max_age,
            )
            mw_change, mw_weight = urgency_from_event(mw_event)

            updated_at = getattr(rec, "updated_at", None) or getattr(
                rec, "created_at", None
            )
            trade_quality = int(getattr(rec, "trade_quality", 0) or 0)
            trade_probability = int(getattr(rec, "trade_probability", 0) or 0)
            confluence = int(getattr(rec, "confluence", 0) or 0)
            setup_quality = int(
                getattr(rec, "setup_quality", None)
                or trade_quality
                or 0
            )
            setup_quality_grade = getattr(rec, "setup_quality_grade", None) or ""
            scanner_group = (
                getattr(rec, "scanner_group", None)
                or scanner_group_for_score(setup_quality, raw_signal)
            )
            rejection_checklist = list(
                getattr(rec, "rejection_checklist", None) or []
            )
            lifecycle_state = getattr(rec, "lifecycle_state", None)
            correlated = bool(getattr(rec, "correlated", False))
            correlation_note = getattr(rec, "correlation_note", None) or ""

            score, breakdown, stale, reasons = rank_opportunity(
                signal=display,
                confidence=confidence,
                trade_quality=setup_quality or trade_quality,
                trade_probability=trade_probability,
                confluence=confluence,
                change_percent=change_pct,
                updated_at=updated_at,
                now=now,
                stale_threshold_minutes=stale_minutes,
                market_watch_change=mw_change,
                market_watch_weight=mw_weight,
                session=session,
            )

            if rec is None:
                # Quote-only row — low score placeholder
                score = max(0, min(40, int(abs(change_pct or 0) * 8)))
                breakdown = ScannerScoreBreakdown(
                    base=0,
                    momentum_align=float(score),
                )
                reasons = ["live quote · no recommendation"]
                stale = True
                scanner_group = "no_trade"
                setup_quality = 0

            if score < min_score_val:
                continue
            if signal_filter and display not in signal_filter and raw_signal not in signal_filter:
                continue
            if actionable_only and display in {"HOLD", "NEUTRAL", "NO_TRADE"}:
                continue

            staleness_ms: int | None = None
            if updated_at is not None:
                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                staleness_ms = int((now - updated_at).total_seconds() * 1000)

            trend = _enum_value(getattr(rec, "trend", None)) or None
            reasoning = getattr(rec, "reasoning", None) if rec else None
            extra_reasons = self._reasoning_list(reasoning)
            merged_reasons = list(dict.fromkeys([*reasons, *extra_reasons]))[:4]
            if correlation_note:
                merged_reasons = list(
                    dict.fromkeys([*merged_reasons, correlation_note])
                )[:4]

            opportunities.append(
                ScannerOpportunityRead(
                    id=f"{symbol}-{tf}",
                    symbol=symbol,
                    timeframe=tf,
                    signal=display,
                    score=score,
                    confidence=confidence,
                    score_breakdown=breakdown,
                    price=price,
                    change_percent=change_pct,
                    entry=_float_or_none(getattr(rec, "entry_price", None)),
                    stop_loss=_float_or_none(getattr(rec, "stop_loss", None)),
                    take_profit=_float_or_none(getattr(rec, "take_profit", None)),
                    risk_reward=_float_or_none(getattr(rec, "risk_reward", None)),
                    trend=trend,
                    confluence=confluence if rec else None,
                    trade_quality=setup_quality if rec else None,
                    trade_probability=trade_probability if rec else None,
                    setup_quality=setup_quality if rec else None,
                    setup_quality_grade=setup_quality_grade or None,
                    scanner_group=str(scanner_group or "no_trade"),
                    rejection_checklist=rejection_checklist,
                    lifecycle_state=lifecycle_state,
                    correlated=correlated,
                    correlation_note=correlation_note,
                    session=session,
                    reasons=merged_reasons,
                    market_watch_tag=mw_change,
                    also_hot_on=also_hot.get(symbol, []),
                    updated_at=updated_at,
                    staleness_ms=staleness_ms,
                    stale=stale,
                    recommendation_id=getattr(rec, "id", None),
                )
            )

        # Institutional ranking + correlation filter across the board
        ranked_payload = [
            {
                "symbol": o.symbol,
                "timeframe": o.timeframe,
                "signal": o.signal,
                "setup_quality": int(o.setup_quality or o.trade_quality or 0),
                "confidence": o.confidence,
                "risk_reward": float(o.risk_reward or 0),
                "trend_strength": 0.0,
                "historical_win_rate": int(o.trade_probability or 0),
                "_opp": o,
            }
            for o in opportunities
        ]
        correlated_rows = filter_correlated(ranked_payload)
        institutional = institutional_rank(correlated_rows)
        by_symbol = {r.symbol: r for r in institutional}

        final_rows: list[ScannerOpportunityRead] = []
        for row in correlated_rows:
            opp: ScannerOpportunityRead = row["_opp"]
            ranked = by_symbol.get(opp.symbol)
            signal = ranked.signal if ranked else opp.signal
            group = ranked.group if ranked else opp.scanner_group
            if row.get("correlated"):
                signal = "HOLD"
                group = "watchlist"
            final_rows.append(
                opp.model_copy(
                    update={
                        "signal": signal,
                        "scanner_group": group,
                        "correlated": bool(row.get("correlated")),
                        "correlation_note": str(row.get("correlation_note") or ""),
                        "score": int(ranked.rank_score) if ranked else opp.score,
                    }
                )
            )

        final_rows.sort(
            key=lambda row: (
                {"elite": 3, "high_quality": 2, "watchlist": 1, "no_trade": 0}.get(
                    row.scanner_group, 0
                ),
                row.score,
                row.confidence,
            ),
            reverse=True,
        )
        if limit is not None and limit > 0:
            # Keep full board for groups, but cap flat list if requested
            final_rows = final_rows[:limit]

        groups = {
            "elite": [o for o in final_rows if o.scanner_group == "elite"],
            "high_quality": [o for o in final_rows if o.scanner_group == "high_quality"],
            "watchlist": [o for o in final_rows if o.scanner_group == "watchlist"],
            "no_trade": [o for o in final_rows if o.scanner_group == "no_trade"],
        }
        group_counts = ScannerGroupCounts(
            elite=len(groups["elite"]),
            high_quality=len(groups["high_quality"]),
            watchlist=len(groups["watchlist"]),
            no_trade=len(groups["no_trade"]),
        )

        mw_meta = scanner_state.snapshot_meta()
        last_scan = mw_meta.get("last_market_watch_scan_at")
        last_scan_age: int | None = None
        if isinstance(last_scan, datetime):
            if last_scan.tzinfo is None:
                last_scan = last_scan.replace(tzinfo=timezone.utc)
            last_scan_age = int((now - last_scan).total_seconds() * 1000)

        # #region agent log
        try:
            import json
            import time
            from pathlib import Path

            _dbg = {
                "sessionId": "e72fc0",
                "runId": "post-fix",
                "hypothesisId": "D",
                "location": "scanner_service.py:get_opportunities",
                "message": "Scanner API group/signal snapshot",
                "data": {
                    "timeframe": tf,
                    "universe": len(universe),
                    "final": len(final_rows),
                    "group_counts": group_counts.model_dump(),
                    "sig_counts": {
                        s: sum(1 for o in final_rows if o.signal == s)
                        for s in {o.signal for o in final_rows}
                    },
                    "sample": [
                        {
                            "symbol": o.symbol,
                            "signal": o.signal,
                            "group": o.scanner_group,
                            "setup_quality": o.setup_quality,
                            "trade_quality": o.trade_quality,
                            "price": o.price,
                        }
                        for o in final_rows[:6]
                    ],
                },
                "timestamp": int(time.time() * 1000),
            }
            Path(__file__).resolve().parents[3].joinpath("debug-e72fc0.log").open(
                "a", encoding="utf-8"
            ).write(json.dumps(_dbg) + "\n")
        except Exception:
            pass
        # #endregion

        return ScannerOpportunitiesResponse(
            opportunities=final_rows,
            groups=groups,
            meta=ScannerMeta(
                timeframe=tf,
                universe_size=len(universe),
                opportunity_count=len(final_rows),
                generated_at=now,
                last_market_watch_scan_at=last_scan
                if isinstance(last_scan, datetime)
                else None,
                last_market_watch_scan_age_ms=last_scan_age,
                stale_threshold_minutes=stale_minutes,
                symbols_scanned=universe,
                group_counts=group_counts,
            ),
        )

    def opportunity_dict_for_broadcast(
        self,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any] | None:
        """Build a single-opportunity payload for WS scanner_update."""
        result = self.get_opportunities(
            timeframe=timeframe,
            symbols=[symbol],
            min_score=0,
        )
        if not result.opportunities:
            return None
        return result.opportunities[0].model_dump(mode="json")

    def _quote_map(self, symbols: list[str], timeframe: str) -> dict[str, float]:
        if not symbols:
            return {}
        try:
            quotes = self.market.get_quotes(symbols, timeframe=timeframe)
        except Exception:
            self.logger.exception("scanner quotes failed")
            return {}
        out: dict[str, float] = {}
        for q in quotes:
            sym = str(getattr(q, "symbol", "")).upper()
            mid = _float_or_none(getattr(q, "mid", None))
            if sym and mid and mid > 0:
                out[sym] = mid
        return out

    def _change_percent_map(
        self,
        symbols: list[str],
        timeframe: str,
        quotes: dict[str, float],
    ) -> dict[str, float]:
        """Change % vs previous candle close (parallel fetch)."""
        from concurrent.futures import ThreadPoolExecutor
        from concurrent.futures import as_completed

        from app.database.database import SessionLocal

        out: dict[str, float] = {}
        if not symbols:
            return out

        def _one(symbol: str) -> tuple[str, float | None]:
            db = SessionLocal()
            try:
                service = MarketService(db)
                candles = service.get_latest_candles(symbol, timeframe, limit=3)
                if not candles:
                    return symbol, None
                latest = candles[-1]
                previous = candles[-2] if len(candles) >= 2 else None
                ref = (
                    _float_or_none(getattr(previous, "close", None))
                    if previous
                    else None
                )
                if ref is None or ref <= 0:
                    ref = _float_or_none(getattr(latest, "open", None))
                live = quotes.get(symbol) or _float_or_none(
                    getattr(latest, "close", None)
                )
                if live is None or ref is None or ref <= 0:
                    return symbol, None
                return symbol, ((live - ref) / ref) * 100.0
            except Exception:
                return symbol, None
            finally:
                db.close()

        workers = min(8, len(symbols))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_one, symbol) for symbol in symbols]
            for fut in as_completed(futures):
                symbol, change = fut.result()
                if change is not None:
                    out[symbol] = change
        return out

    def _also_hot_map(
        self,
        symbols: list[str],
        primary_tf: str,
    ) -> dict[str, list[str]]:
        """Secondary TFs where latest recommendation is actionable and confident."""
        secondary = [
            tf.upper()
            for tf in settings.SCANNER_SECONDARY_TIMEFRAMES
            if tf.upper() in SUPPORTED_TIMEFRAMES and tf.upper() != primary_tf.upper()
        ]
        if not secondary or not symbols:
            return {}

        hot: dict[str, list[str]] = {s: [] for s in symbols}
        strong = int(settings.SCANNER_STRONG_SIGNAL_CONFIDENCE)
        for tf in secondary:
            batch = self.recommendations.get_latest_for_symbols(symbols, tf)
            for symbol, rec in batch.items():
                signal = _enum_value(rec.signal).upper()
                conf = int(rec.confidence or 0)
                if signal in {"HOLD", "NO_TRADE", "NEUTRAL"}:
                    continue
                if conf < max(50, strong - 15):
                    continue
                hot.setdefault(symbol, []).append(tf)
        return {k: v for k, v in hot.items() if v}

    @staticmethod
    def _reasoning_list(reasoning: Any) -> list[str]:
        if reasoning is None:
            return []
        if isinstance(reasoning, list):
            return [str(x) for x in reasoning if x][:3]
        if isinstance(reasoning, str) and reasoning.strip():
            return [reasoning.strip()[:120]]
        return []
