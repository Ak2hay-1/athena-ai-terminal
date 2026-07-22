"""
User preferences API.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.repositories.preferences_repository import PreferencesRepository
from app.services.base_service import BaseService

router = APIRouter(
    prefix="/preferences",
    tags=["Preferences"],
)


class PreferencesUpdate(BaseModel):
    timezone: str | None = None
    language: str | None = None
    trading_style: str | None = None
    risk_profile: str | None = None
    preferred_channel: str | None = None
    notification_frequency: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    preferred_sessions: list[str] | None = None
    preferred_timeframes: list[str] | None = None
    preferred_strategies: list[str] | None = None
    ignored_symbols: list[str] | None = None
    favorite_assets: list[str] | None = None
    preferred_rr: float | None = None
    telegram_chat_id: str | None = None
    discord_webhook_url: str | None = None
    email_override: str | None = None
    push_device_token: str | None = None
    auto_trade_enabled: bool | None = None
    auto_trade_symbols: list[str] | None = None
    auto_trade_timeframes: list[str] | None = None
    auto_trade_min_confidence: int | None = Field(default=None, ge=0, le=100)
    auto_trade_min_confluence: int | None = Field(default=None, ge=0, le=100)
    auto_trade_min_rr: float | None = Field(default=None, ge=0)
    auto_trade_volume: float | None = Field(default=None, gt=0, le=100)


class PreferencesRead(BaseModel):
    user_id: int
    timezone: str
    language: str
    trading_style: str
    risk_profile: str
    preferred_channel: str
    notification_frequency: str
    quiet_hours_start: str
    quiet_hours_end: str
    preferred_sessions: list[str] = Field(default_factory=list)
    preferred_timeframes: list[str] = Field(default_factory=list)
    preferred_strategies: list[str] = Field(default_factory=list)
    ignored_symbols: list[str] = Field(default_factory=list)
    favorite_assets: list[str] = Field(default_factory=list)
    preferred_rr: float | None = None
    telegram_chat_id: str | None = None
    discord_webhook_url: str | None = None
    email_override: str | None = None
    auto_trade_enabled: bool = False
    auto_trade_symbols: list[str] = Field(default_factory=list)
    auto_trade_timeframes: list[str] = Field(default_factory=list)
    auto_trade_min_confidence: int = 70
    auto_trade_min_confluence: int = 0
    auto_trade_min_rr: float = 0.0
    auto_trade_volume: float = 0.01

    model_config = {"from_attributes": True}


def _to_read(row: UserPreferences) -> PreferencesRead:
    return PreferencesRead(
        user_id=row.user_id,
        timezone=row.timezone,
        language=row.language,
        trading_style=row.trading_style,
        risk_profile=row.risk_profile,
        preferred_channel=row.preferred_channel,
        notification_frequency=row.notification_frequency,
        quiet_hours_start=row.quiet_hours_start,
        quiet_hours_end=row.quiet_hours_end,
        preferred_sessions=list(row.preferred_sessions or []),
        preferred_timeframes=list(row.preferred_timeframes or []),
        preferred_strategies=list(row.preferred_strategies or []),
        ignored_symbols=[str(s).upper() for s in (row.ignored_symbols or [])],
        favorite_assets=[str(s).upper() for s in (row.favorite_assets or [])],
        preferred_rr=row.preferred_rr,
        telegram_chat_id=row.telegram_chat_id,
        discord_webhook_url=row.discord_webhook_url,
        email_override=row.email_override,
        auto_trade_enabled=bool(row.auto_trade_enabled),
        auto_trade_symbols=[str(s).upper() for s in (row.auto_trade_symbols or [])],
        auto_trade_timeframes=[
            str(t).upper() for t in (row.auto_trade_timeframes or [])
        ],
        auto_trade_min_confidence=int(row.auto_trade_min_confidence or 70),
        auto_trade_min_confluence=int(row.auto_trade_min_confluence or 0),
        auto_trade_min_rr=float(row.auto_trade_min_rr or 0.0),
        auto_trade_volume=float(row.auto_trade_volume or 0.01),
    )


class PreferencesService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.repository = PreferencesRepository(db)

    def get(self, user_id: int) -> UserPreferences:
        return self.repository.get_or_create(user_id)

    def update(self, user_id: int, payload: PreferencesUpdate) -> UserPreferences:
        row = self.repository.get_or_create(user_id)
        data = payload.model_dump(exclude_unset=True)
        if "ignored_symbols" in data and data["ignored_symbols"] is not None:
            data["ignored_symbols"] = [str(s).upper() for s in data["ignored_symbols"]]
        if "favorite_assets" in data and data["favorite_assets"] is not None:
            data["favorite_assets"] = [str(s).upper() for s in data["favorite_assets"]]
        if "auto_trade_symbols" in data and data["auto_trade_symbols"] is not None:
            data["auto_trade_symbols"] = [
                str(s).upper() for s in data["auto_trade_symbols"]
            ]
        if "auto_trade_timeframes" in data and data["auto_trade_timeframes"] is not None:
            data["auto_trade_timeframes"] = [
                str(t).upper() for t in data["auto_trade_timeframes"]
            ]
        row.update(**data)
        self.commit()
        self.refresh(row)
        return row


@router.get("", response_model=PreferencesRead)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PreferencesRead:
    service = PreferencesService(db)
    return _to_read(service.get(current_user.id))


@router.put("", response_model=PreferencesRead)
async def put_preferences(
    payload: PreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PreferencesRead:
    service = PreferencesService(db)
    return _to_read(service.update(current_user.id, payload))
