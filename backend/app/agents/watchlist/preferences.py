"""
Load watchlist + user preference context.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.repositories.preferences_repository import PreferencesRepository
from app.repositories.watchlist_repository import WatchlistRepository


@dataclass
class UserWatchContext:
    user_id: int
    symbols: set[str] = field(default_factory=set)
    symbol_timeframes: set[tuple[str, str]] = field(default_factory=set)
    ignored_symbols: set[str] = field(default_factory=set)
    preferred_sessions: set[str] = field(default_factory=set)
    preferred_timeframes: set[str] = field(default_factory=set)
    preferred_strategies: set[str] = field(default_factory=set)


def load_watch_contexts(db: Session | None = None) -> list[UserWatchContext]:
    own = db is None
    session = db or SessionLocal()
    try:
        watch_repo = WatchlistRepository(session)
        prefs_repo = PreferencesRepository(session)
        # Group watchlist by user
        from sqlalchemy import select

        from app.models.user_watchlist import UserWatchlist

        rows = list(
            session.scalars(
                select(UserWatchlist).where(UserWatchlist.enabled.is_(True))
            ).all()
        )
        by_user: dict[int, UserWatchContext] = {}
        for row in rows:
            ctx = by_user.setdefault(row.user_id, UserWatchContext(user_id=row.user_id))
            symbol = str(row.symbol).upper()
            tf = str(row.timeframe).upper()
            ctx.symbols.add(symbol)
            ctx.symbol_timeframes.add((symbol, tf))

        for user_id, ctx in by_user.items():
            prefs = prefs_repo.get_for_user(user_id)
            if prefs is None:
                continue
            ctx.ignored_symbols = {
                str(s).upper() for s in (prefs.ignored_symbols or [])
            }
            ctx.preferred_sessions = {
                str(s).lower() for s in (prefs.preferred_sessions or [])
            }
            ctx.preferred_timeframes = {
                str(s).upper() for s in (prefs.preferred_timeframes or [])
            }
            ctx.preferred_strategies = {
                str(s).lower() for s in (prefs.preferred_strategies or [])
            }
            for asset in prefs.favorite_assets or []:
                ctx.symbols.add(str(asset).upper())

        return list(by_user.values())
    finally:
        if own:
            session.close()


def load_context_for_user(user_id: int) -> UserWatchContext | None:
    contexts = load_watch_contexts()
    for ctx in contexts:
        if ctx.user_id == user_id:
            return ctx
    return None
