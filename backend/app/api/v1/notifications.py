"""
Notification history and interaction API.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.user import User
from app.personalization.tracker import record_interaction
from app.repositories.notification_repository import NotificationRepository

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


class NotificationRead(BaseModel):
    id: int
    channel: str
    message_type: str
    priority: str
    status: str
    payload: dict
    latency_ms: float | None = None
    created_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    dismissed_at: datetime | None = None

    model_config = {"from_attributes": True}


class InteractRequest(BaseModel):
    action: str = Field(..., examples=["opened", "clicked", "dismissed"])


@router.get("/recent", response_model=list[NotificationRead])
async def recent_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[NotificationRead]:
    repo = NotificationRepository(db)
    rows = repo.recent_for_user(current_user.id, limit=max(1, min(limit, 200)))
    return [NotificationRead.model_validate(r) for r in rows]


@router.post("/{delivery_id}/interact", response_model=NotificationRead)
async def interact_notification(
    delivery_id: int,
    payload: InteractRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    action = payload.action.lower().strip()
    if action not in {"opened", "clicked", "dismissed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action must be opened, clicked, or dismissed",
        )
    repo = NotificationRepository(db)
    row = repo.get_for_user(delivery_id, current_user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    now = datetime.now(timezone.utc)
    if action == "opened" and row.opened_at is None:
        row.opened_at = now
    elif action == "clicked" and row.clicked_at is None:
        row.clicked_at = now
        if row.opened_at is None:
            row.opened_at = now
    elif action == "dismissed" and row.dismissed_at is None:
        row.dismissed_at = now

    repo.db.commit()
    repo.db.refresh(row)
    record_interaction(db, user_id=current_user.id, delivery=row, action=action)
    return NotificationRead.model_validate(row)
