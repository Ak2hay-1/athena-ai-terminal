"""
Portfolio awareness — reject setups that worsen book risk.
"""

from __future__ import annotations

from collections import Counter
from typing import Any
from typing import Iterable

from app.core.settings import settings
from app.qualification.correlation_filter import conflicts_with_open
from app.qualification.correlation_filter import correlation_bucket


def evaluate_portfolio_fit(
    *,
    symbol: str,
    signal: str,
    risk_percent: float | None = None,
    open_trades: Iterable[dict[str, Any]] | None = None,
) -> tuple[bool, list[str]]:
    """
    Returns (allowed, reasons).

    open_trades items: {symbol, signal|side, risk_percent?}
    """
    reasons: list[str] = []
    trades = list(open_trades or [])
    sig = signal.upper()

    if sig not in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
        return True, reasons

    # Max simultaneous positions
    max_open = int(settings.MAX_OPEN_TRADES)
    if len(trades) >= max_open:
        reasons.append(f"Max open trades reached ({max_open}).")

    buys = sum(1 for t in trades if "BUY" in str(t.get("signal") or t.get("side") or "").upper())
    sells = sum(1 for t in trades if "SELL" in str(t.get("signal") or t.get("side") or "").upper())
    max_buys = int(settings.MAX_SIMULTANEOUS_BUYS)
    max_sells = int(settings.MAX_SIMULTANEOUS_SELLS)

    if "BUY" in sig and buys >= max_buys:
        reasons.append(f"Max simultaneous buys reached ({max_buys}).")
    if "SELL" in sig and sells >= max_sells:
        reasons.append(f"Max simultaneous sells reached ({max_sells}).")

    # Currency / correlated exposure
    conflict, note = conflicts_with_open(symbol=symbol, signal=sig, open_trades=trades)
    if conflict:
        reasons.append(note or "Correlated exposure limit.")

    # Max correlated in same bucket
    max_corr = int(settings.MAX_CORRELATED_EXPOSURE)
    buckets = correlation_bucket(symbol, sig)
    for bucket in buckets:
        count = 0
        for t in trades:
            other_sig = str(t.get("signal") or t.get("side") or "").upper()
            other_buckets = correlation_bucket(str(t.get("symbol") or ""), other_sig)
            if bucket in other_buckets:
                count += 1
        if count >= max_corr:
            reasons.append(f"Max correlated exposure in {bucket} ({max_corr}).")

    # Aggregate risk %
    max_risk = float(settings.MAX_PORTFOLIO_RISK_PERCENT)
    current_risk = sum(float(t.get("risk_percent") or 0.0) for t in trades)
    add_risk = float(risk_percent if risk_percent is not None else settings.MAX_RISK_PERCENT)
    if current_risk + add_risk > max_risk:
        reasons.append(
            f"Portfolio risk {current_risk + add_risk:.1f}% exceeds max {max_risk:.1f}%."
        )

    # Same symbol already open
    if any(str(t.get("symbol") or "").upper() == symbol.upper() for t in trades):
        reasons.append(f"Open position already exists on {symbol}.")

    return (len(reasons) == 0), reasons


def currency_exposure_summary(open_trades: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count how many open trades touch each currency code."""
    counter: Counter[str] = Counter()
    for trade in open_trades:
        sym = str(trade.get("symbol") or "").upper()
        if len(sym) >= 6:
            counter[sym[:3]] += 1
            counter[sym[3:6]] += 1
    return dict(counter)
