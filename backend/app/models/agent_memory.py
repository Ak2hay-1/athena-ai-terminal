"""
Agent trading-intelligence memory model.
"""

from __future__ import annotations

from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class AgentMemory(BaseModel):
    """
    Persisted trading intelligence for agents.

    Not conversation memory — observations, decisions, outcomes, stats, feedback.
    """

    __tablename__ = "agent_memories"

    __table_args__ = (
        Index("idx_agent_memories_agent_type", "agent_id", "memory_type"),
        Index("idx_agent_memories_symbol", "symbol"),
        Index("idx_agent_memories_correlation", "correlation_id"),
    )

    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    memory_type: Mapped[str] = mapped_column(String(32), nullable=False)

    symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)

    timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)

    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
