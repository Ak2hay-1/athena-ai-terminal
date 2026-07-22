"""
Watchlist filtering helpers.
"""

from __future__ import annotations

from typing import Any

from app.agents.watchlist.preferences import UserWatchContext


def matches_watchlist(
    ctx: UserWatchContext,
    *,
    symbol: str,
    timeframe: str | None = None,
    session: str | None = None,
) -> bool:
    symbol_u = str(symbol or "").upper()
    if not symbol_u:
        return False
    if symbol_u in ctx.ignored_symbols:
        return False
    if symbol_u not in ctx.symbols:
        return False

    tf = str(timeframe or "").upper()
    if tf and ctx.symbol_timeframes:
        # Prefer exact (symbol, tf) if user configured pairs
        if (symbol_u, tf) in ctx.symbol_timeframes:
            return _session_ok(ctx, session)
        # Allow symbol-only favorites from preferences without TF pairs
        has_symbol_pair = any(s == symbol_u for s, _ in ctx.symbol_timeframes)
        if has_symbol_pair:
            if ctx.preferred_timeframes and tf and tf not in ctx.preferred_timeframes:
                return False
            return _session_ok(ctx, session)
        return False

    if ctx.preferred_timeframes and tf and tf not in ctx.preferred_timeframes:
        return False
    return _session_ok(ctx, session)


def _session_ok(ctx: UserWatchContext, session: str | None) -> bool:
    if not ctx.preferred_sessions:
        return True
    if not session:
        return True
    return str(session).lower() in ctx.preferred_sessions


def filter_payload_for_users(
    contexts: list[UserWatchContext],
    payload: dict[str, Any],
) -> list[UserWatchContext]:
    symbol = str(payload.get("symbol") or "")
    timeframe = str(payload.get("timeframe") or "")
    session = payload.get("session")
    if isinstance(session, list) and session:
        session = session[0]
    matched: list[UserWatchContext] = []
    for ctx in contexts:
        if matches_watchlist(
            ctx,
            symbol=symbol,
            timeframe=timeframe,
            session=str(session) if session else None,
        ):
            matched.append(ctx)
    return matched
