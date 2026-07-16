"""
User watchlist repository.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user_watchlist import UserWatchlist
from app.repositories.base_repository import BaseRepository


class WatchlistRepository(BaseRepository[UserWatchlist]):
    """
    User watchlist persistence.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, UserWatchlist)

    def list_for_user(
        self,
        user_id: int,
    ) -> list[UserWatchlist]:
        return (
            self.db.query(UserWatchlist)
            .filter(UserWatchlist.user_id == user_id)
            .order_by(UserWatchlist.symbol)
            .all()
        )

    def get_entry(
        self,
        user_id: int,
        symbol: str,
        timeframe: str,
    ) -> UserWatchlist | None:
        return (
            self.db.query(UserWatchlist)
            .filter(
                UserWatchlist.user_id == user_id,
                UserWatchlist.symbol == symbol.upper(),
                UserWatchlist.timeframe == timeframe.upper(),
            )
            .first()
        )
