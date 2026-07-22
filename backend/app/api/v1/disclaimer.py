"""
Risk disclaimer API.

Persists acceptance on user_preferences and gates terminal access until
the latest DISCLAIMER_VERSION has been accepted.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.core.disclaimer import DISCLAIMER_VERSION
from app.database.database import get_db
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.repositories.preferences_repository import PreferencesRepository
from app.schemas.disclaimer import DisclaimerAcceptRequest
from app.schemas.disclaimer import DisclaimerStatus
from app.services.base_service import BaseService

router = APIRouter(
    prefix="/disclaimer",
    tags=["Disclaimer"],
)


def _is_current_acceptance(prefs: UserPreferences) -> bool:
    return bool(
        prefs.risk_disclaimer_accepted
        and prefs.risk_disclaimer_version == DISCLAIMER_VERSION
    )


def _to_status(prefs: UserPreferences) -> DisclaimerStatus:
    accepted = _is_current_acceptance(prefs)
    return DisclaimerStatus(
        accepted=accepted,
        accepted_at=prefs.risk_disclaimer_accepted_at if accepted else None,
        disclaimer_version=prefs.risk_disclaimer_version if accepted else None,
        app_version=prefs.risk_disclaimer_app_version if accepted else None,
        required_version=DISCLAIMER_VERSION,
    )


class DisclaimerService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.repository = PreferencesRepository(db)

    def get_status(self, user_id: int) -> DisclaimerStatus:
        prefs = self.repository.get_or_create(user_id)
        return _to_status(prefs)

    def accept(
        self,
        user_id: int,
        *,
        app_version: str,
        disclaimer_version: str | None,
    ) -> DisclaimerStatus:
        version = (disclaimer_version or DISCLAIMER_VERSION).strip()
        if version != DISCLAIMER_VERSION:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Disclaimer version mismatch. "
                    f"Required: {DISCLAIMER_VERSION}, received: {version}."
                ),
            )

        prefs = self.repository.get_or_create(user_id)
        prefs.update(
            risk_disclaimer_accepted=True,
            risk_disclaimer_accepted_at=datetime.now(timezone.utc),
            risk_disclaimer_version=DISCLAIMER_VERSION,
            risk_disclaimer_app_version=app_version.strip()[:32],
        )
        self.commit()
        self.refresh(prefs)
        return _to_status(prefs)

    def has_accepted_current(self, user_id: int) -> bool:
        prefs = self.repository.get_or_create(user_id)
        return _is_current_acceptance(prefs)


@router.get("", response_model=DisclaimerStatus)
async def get_disclaimer_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DisclaimerStatus:
    """Return whether the user has accepted the latest risk disclaimer."""
    return DisclaimerService(db).get_status(current_user.id)


@router.post("/accept", response_model=DisclaimerStatus)
async def accept_disclaimer(
    payload: DisclaimerAcceptRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DisclaimerStatus:
    """Record acceptance of the current risk disclaimer version."""
    return DisclaimerService(db).accept(
        current_user.id,
        app_version=payload.app_version,
        disclaimer_version=payload.disclaimer_version,
    )
