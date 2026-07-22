"""
Per-user trading and notification preferences.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class UserPreferences(BaseModel):
    """
    Personalization and notification preferences for a user.
    """

    __tablename__ = "user_preferences"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preferences_user"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
    )

    language: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="en",
    )

    trading_style: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="intraday",
    )

    risk_profile: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="balanced",
    )

    preferred_channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="websocket",
    )

    notification_frequency: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="normal",
    )

    quiet_hours_start: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="22:00",
    )

    quiet_hours_end: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="07:00",
    )

    preferred_sessions: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    preferred_timeframes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    preferred_strategies: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    ignored_symbols: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    favorite_assets: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    preferred_rr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    soft_weights: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    discord_webhook_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    email_override: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    push_device_token: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # Risk disclaimer acceptance (legal gate for terminal access)
    risk_disclaimer_accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    risk_disclaimer_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    risk_disclaimer_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    risk_disclaimer_app_version: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # Auto-trade (server-side signal → order)
    auto_trade_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    auto_trade_symbols: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    auto_trade_timeframes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    auto_trade_min_confidence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
        server_default="70",
    )

    auto_trade_min_confluence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    auto_trade_min_rr: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0",
    )

    auto_trade_volume: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.01,
        server_default="0.01",
    )
