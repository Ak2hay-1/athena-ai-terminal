"""
News Event Model.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class NewsImpact(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NewsEvent(BaseModel):
    """
    Economic news or headline event.
    """

    __tablename__ = "news_events"

    __table_args__ = (
        Index("idx_news_published_at", "published_at"),
        Index("idx_news_impact", "impact"),
    )

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="rss",
    )

    symbols: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)),
        nullable=False,
        default=list,
    )

    impact: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=NewsImpact.MEDIUM.value,
    )

    sentiment_score: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        unique=True,
    )
