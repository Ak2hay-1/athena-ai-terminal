"""
Correlation filter — avoid stacking highly correlated directional exposure.
"""

from __future__ import annotations

from typing import Any
from typing import Iterable

from app.core.settings import settings


# Default FX correlation buckets (USD majors + crosses).
DEFAULT_CORRELATION_GROUPS: dict[str, list[str]] = {
    "USD_LONG": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],  # BUY = short USD
    "USD_SHORT": ["USDJPY", "USDCHF", "USDCAD"],  # BUY = long USD
    "JPY_CROSSES": ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "NZDJPY"],
    "EUR_CROSSES": ["EURGBP", "EURJPY", "EURCHF", "EURAUD"],
    "GOLD": ["XAUUSD", "XAGUSD"],
}


def _groups() -> dict[str, list[str]]:
    configured = getattr(settings, "CORRELATION_GROUPS", None) or {}
    if configured:
        return {k: [s.upper() for s in v] for k, v in configured.items()}
    return {k: [s.upper() for s in v] for k, v in DEFAULT_CORRELATION_GROUPS.items()}


def _usd_direction_key(symbol: str, signal: str) -> str | None:
    """Map symbol+signal to a USD-exposure key for majors."""
    sym = symbol.upper()
    sig = signal.upper()
    is_buy = "BUY" in sig
    # XXXUSD BUY ⇒ short USD; SELL ⇒ long USD
    if sym.endswith("USD") and not sym.startswith("USD") and len(sym) == 6:
        return "SHORT_USD" if is_buy else "LONG_USD"
    # USDXXX BUY ⇒ long USD; SELL ⇒ short USD
    if sym.startswith("USD") and len(sym) == 6:
        return "LONG_USD" if is_buy else "SHORT_USD"
    return None


def correlation_bucket(symbol: str, signal: str) -> list[str]:
    """Return correlation bucket ids this trade belongs to."""
    buckets: list[str] = []
    sym = symbol.upper()
    for name, members in _groups().items():
        if sym in members:
            buckets.append(name)
    usd = _usd_direction_key(sym, signal)
    if usd:
        buckets.append(usd)
    return buckets


def is_correlated(
    symbol_a: str,
    signal_a: str,
    symbol_b: str,
    signal_b: str,
) -> bool:
    if symbol_a.upper() == symbol_b.upper():
        return False
    a = set(correlation_bucket(symbol_a, signal_a))
    b = set(correlation_bucket(symbol_b, signal_b))
    if not a or not b:
        return False
    # Same named group + same directional USD exposure when applicable
    shared = a & b
    if not shared:
        return False
    # If only sharing a named FX group, require same side on both
    named = {x for x in shared if x not in {"LONG_USD", "SHORT_USD"}}
    usd_shared = shared & {"LONG_USD", "SHORT_USD"}
    if usd_shared:
        return True
    if named:
        # Same basket — correlated if same signal direction
        a_buy = "BUY" in signal_a.upper()
        b_buy = "BUY" in signal_b.upper()
        return a_buy == b_buy
    return False


def filter_correlated(
    items: Iterable[dict[str, Any]],
    *,
    allow_multiple: bool | None = None,
    quality_key: str = "setup_quality",
) -> list[dict[str, Any]]:
    """
    Keep the highest-quality setup per correlation cluster.

    Demoted items get:
      correlated=True
      signal overridden to HOLD (Correlated Opportunity)
      correlation_note set
    """
    allow = (
        bool(settings.ALLOW_CORRELATED_TRADES)
        if allow_multiple is None
        else bool(allow_multiple)
    )
    rows = [dict(item) for item in items]
    if allow:
        for row in rows:
            row.setdefault("correlated", False)
            row.setdefault("correlation_note", "")
        return rows

    # Sort best-first
    rows.sort(
        key=lambda r: (
            int(r.get(quality_key) or r.get("trade_quality") or 0),
            int(r.get("confidence") or 0),
            float(r.get("risk_reward") or 0),
        ),
        reverse=True,
    )

    kept: list[dict[str, Any]] = []
    for row in rows:
        signal = str(row.get("signal") or "").upper()
        if signal not in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
            row["correlated"] = False
            row["correlation_note"] = ""
            kept.append(row)
            continue

        conflict_with = None
        for winner in kept:
            w_sig = str(winner.get("signal") or "").upper()
            if w_sig not in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
                continue
            if is_correlated(
                str(row.get("symbol") or ""),
                signal,
                str(winner.get("symbol") or ""),
                w_sig,
            ):
                conflict_with = winner
                break

        if conflict_with is not None:
            row["correlated"] = True
            row["correlation_note"] = (
                f"Correlated Opportunity vs {conflict_with.get('symbol')} "
                f"({conflict_with.get('signal')})"
            )
            row["signal"] = "HOLD"
            row["scanner_group"] = "watchlist"
        else:
            row["correlated"] = False
            row["correlation_note"] = ""
        kept.append(row)

    return kept


def conflicts_with_open(
    *,
    symbol: str,
    signal: str,
    open_trades: Iterable[dict[str, Any]],
) -> tuple[bool, str]:
    """Check a candidate against already-open / already-recommended trades."""
    if settings.ALLOW_CORRELATED_TRADES:
        return False, ""
    for trade in open_trades:
        other_sym = str(trade.get("symbol") or "")
        other_sig = str(trade.get("signal") or trade.get("side") or "").upper()
        if other_sig not in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
            continue
        if is_correlated(symbol, signal, other_sym, other_sig):
            return True, f"Correlated with open {other_sym} {other_sig}"
    return False, ""
