"""
Server-side auto-trade: execute orders when Athena emits actionable signals.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.models import AIRecommendation
from app.core.enums import RecommendationSignal
from app.core.logger import logger
from app.core.settings import settings
from app.models.user_preferences import UserPreferences
from app.repositories.preferences_repository import PreferencesRepository
from app.trading.order_manager import order_manager

_NON_ACTIONABLE = frozenset({"HOLD", "NO_TRADE", "WAIT", "NEUTRAL"})


def _signal_value(recommendation: AIRecommendation) -> str:
    signal = recommendation.signal
    if hasattr(signal, "value"):
        signal = signal.value
    return str(signal).upper()


def _normalize_actionable(signal: str) -> str | None:
    if signal in _NON_ACTIONABLE:
        return None
    if signal == "STRONG_BUY":
        return "BUY"
    if signal == "STRONG_SELL":
        return "SELL"
    if signal in ("BUY", "SELL"):
        return signal
    return None


class AutoTradeService:
    """
    Apply per-user auto-trade filters and place MT5 orders via OrderManager.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.prefs_repo = PreferencesRepository(db)

    def process(self, recommendation: AIRecommendation) -> list[dict[str, Any]]:
        raw_signal = _signal_value(recommendation)
        actionable = _normalize_actionable(raw_signal)
        if actionable is None:
            return []

        symbol = str(recommendation.symbol or "").upper()
        timeframe = str(recommendation.timeframe or "").upper()
        if not symbol or not timeframe:
            logger.warning("Auto-trade skipped: missing symbol/timeframe")
            return []

        # Normalize recommendation signal for execution
        recommendation.signal = (
            RecommendationSignal.BUY if actionable == "BUY" else RecommendationSignal.SELL
        )
        recommendation.symbol = symbol
        recommendation.timeframe = timeframe

        enabled_prefs = self.prefs_repo.list_auto_trade_enabled()
        if not enabled_prefs:
            return []

        results: list[dict[str, Any]] = []
        mt5_executed = False

        for prefs in enabled_prefs:
            matched, reason = self._passes_filters(prefs, recommendation)
            if not matched:
                logger.info(
                    "Auto-trade skip user=%s %s %s: %s",
                    prefs.user_id,
                    symbol,
                    timeframe,
                    reason,
                )
                continue

            if mt5_executed:
                logger.info(
                    "Auto-trade skip user=%s %s %s: MT5 order already placed",
                    prefs.user_id,
                    symbol,
                    timeframe,
                )
                continue

            if self._has_open_symbol(symbol):
                logger.info(
                    "Auto-trade skip %s: open/pending MT5 position exists",
                    symbol,
                )
                continue

            if self._at_max_trades():
                logger.info("Auto-trade skip: max MT5 open trades reached")
                continue

            volume = float(prefs.auto_trade_volume or settings.DEFAULT_VOLUME)
            try:
                result = order_manager.execute(
                    recommendation,
                    volume=volume,
                    user_id=prefs.user_id,
                    source="auto",
                )
            except Exception as exc:
                logger.exception(
                    "Auto-trade MT5 execution failed user=%s %s %s",
                    prefs.user_id,
                    symbol,
                    timeframe,
                )
                results.append(
                    {
                        "user_id": prefs.user_id,
                        "success": False,
                        "reasons": [str(exc)],
                    }
                )
                continue

            success = bool(result.get("success"))
            if success:
                mt5_executed = True

            logger.info(
                "Auto-trade MT5 user=%s %s %s %s success=%s",
                prefs.user_id,
                symbol,
                timeframe,
                actionable,
                success,
            )
            results.append({"user_id": prefs.user_id, **result})

        return results

    def _passes_filters(
        self,
        prefs: UserPreferences,
        recommendation: AIRecommendation,
    ) -> tuple[bool, str]:
        symbol = str(recommendation.symbol or "").upper()
        timeframe = str(recommendation.timeframe or "").upper()

        symbols = [str(s).upper() for s in (prefs.auto_trade_symbols or [])]
        if symbols and symbol not in symbols:
            return False, f"symbol {symbol} not in filter"

        timeframes = [str(t).upper() for t in (prefs.auto_trade_timeframes or [])]
        if timeframes and timeframe not in timeframes:
            return False, f"timeframe {timeframe} not in filter"

        confidence = int(recommendation.confidence or 0)
        min_confidence = int(prefs.auto_trade_min_confidence or 0)
        if confidence < min_confidence:
            return False, f"confidence {confidence} < {min_confidence}"

        min_confluence = int(prefs.auto_trade_min_confluence or 0)
        if min_confluence > 0:
            confluence = int(recommendation.confluence or 0)
            if confluence < min_confluence:
                return False, f"confluence {confluence} < {min_confluence}"

        min_rr = float(prefs.auto_trade_min_rr or 0.0)
        if min_rr > 0:
            rr = float(recommendation.risk_reward or 0.0)
            if rr < min_rr:
                return False, f"risk_reward {rr} < {min_rr}"

        # Institutional desk: only auto-trade high-quality actionable setups
        setup_quality = int(
            getattr(recommendation, "setup_quality", 0)
            or getattr(recommendation, "trade_quality", 0)
            or 0
        )
        min_quality = int(settings.MIN_SETUP_QUALITY)
        if setup_quality < min_quality:
            return False, f"setup_quality {setup_quality} < {min_quality}"

        scanner_group = str(getattr(recommendation, "scanner_group", "") or "")
        if scanner_group in {"watchlist", "no_trade"}:
            return False, f"scanner_group={scanner_group}"

        if getattr(recommendation, "correlated", False) and not settings.ALLOW_CORRELATED_TRADES:
            return False, "correlated opportunity blocked"

        return True, "ok"

    def _has_open_symbol(self, symbol: str) -> bool:
        symbol = symbol.upper()
        try:
            positions = order_manager.positions()
        except Exception:
            logger.exception("Failed to list MT5 positions for auto-trade")
            return True

        for row in positions or []:
            row_symbol = str(row.get("symbol") or "").upper()
            status = str(row.get("status") or "").upper()
            if row_symbol == symbol and status in ("", "OPEN", "PENDING", "LIVE"):
                return True
        return False

    def _at_max_trades(self) -> bool:
        max_open = int(settings.MAX_OPEN_TRADES)
        try:
            positions = order_manager.positions() or []
            return len(positions) >= max_open
        except Exception:
            logger.exception("Failed counting MT5 positions for auto-trade")
            return True
