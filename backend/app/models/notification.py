"""
Notification delivery and interaction models.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class NotificationDelivery(BaseModel):
    """
    Persisted notification dispatch attempt for observability.
    """

    __tablename__ = "notification_deliveries"

    __table_args__ = (
        Index("idx_notification_deliveries_user", "user_id"),
        Index("idx_notification_deliveries_dedupe", "dedupe_key"),
        Index("idx_notification_deliveries_status", "status"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="Medium",
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="queued",
    )

    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    dedupe_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )


class NotificationInteraction(BaseModel):
    """
    User interaction with a delivered notification.
    """

    __tablename__ = "notification_interactions"

    __table_args__ = (
        Index("idx_notification_interactions_delivery", "delivery_id"),
    )

    delivery_id: Mapped[int] = mapped_column(
        ForeignKey("notification_deliveries.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )
