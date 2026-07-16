"""
User watchlist API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe
from app.database.database import get_db
from app.models.user import User
from app.models.user_watchlist import UserWatchlist
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.base_service import BaseService

router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"],
)


class WatchlistCreate(BaseModel):
    symbol: str = Field(..., examples=["EURUSD"])
    timeframe: str = Field(..., examples=["M15"])
    enabled: bool = True


class WatchlistRead(BaseModel):
    id: int
    symbol: str
    timeframe: str
    enabled: bool

    model_config = {"from_attributes": True}


class WatchlistService(BaseService):

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.repository = WatchlistRepository(db)

    def list_entries(
        self,
        user_id: int,
    ) -> list[UserWatchlist]:
        return self.repository.list_for_user(user_id)

    def add(
        self,
        user_id: int,
        payload: WatchlistCreate,
    ) -> UserWatchlist:
        symbol = validate_symbol(payload.symbol)
        timeframe = validate_timeframe(payload.timeframe)

        existing = self.repository.get_entry(
            user_id,
            symbol,
            timeframe,
        )

        if existing:
            existing.enabled = payload.enabled
            self.commit()
            return existing

        entry = UserWatchlist(
            user_id=user_id,
            symbol=symbol,
            timeframe=timeframe,
            enabled=payload.enabled,
        )

        self.repository.create(entry)
        self.commit()
        self.refresh(entry)
        return entry

    def remove(
        self,
        user_id: int,
        entry_id: int,
    ) -> None:
        entry = self.repository.get_by_id(entry_id)

        if entry is None or entry.user_id != user_id:
            return

        self.repository.delete(entry)
        self.commit()


def get_watchlist_service(
    db: Session = Depends(get_db),
) -> WatchlistService:
    return WatchlistService(db)


@router.get(
    "",
    response_model=list[WatchlistRead],
)
def list_watchlist(
    user: User = Depends(get_current_active_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.list_entries(user.id)


@router.post(
    "",
    response_model=WatchlistRead,
    status_code=status.HTTP_201_CREATED,
)
def add_watchlist(
    payload: WatchlistCreate,
    user: User = Depends(get_current_active_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.add(user.id, payload)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_watchlist(
    entry_id: int,
    user: User = Depends(get_current_active_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    service.remove(user.id, entry_id)
