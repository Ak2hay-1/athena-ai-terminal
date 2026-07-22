"""
Repository for agent trading memory.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_memory import AgentMemory
from app.repositories.base_repository import BaseRepository


class MemoryRepository(BaseRepository[AgentMemory]):
    """Data access for AgentMemory rows."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, AgentMemory)

    def query(
        self,
        *,
        agent_id: str | None = None,
        memory_type: str | None = None,
        symbol: str | None = None,
        correlation_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AgentMemory]:
        stmt = select(AgentMemory)

        if agent_id is not None:
            stmt = stmt.where(AgentMemory.agent_id == agent_id)
        if memory_type is not None:
            stmt = stmt.where(AgentMemory.memory_type == memory_type)
        if symbol is not None:
            stmt = stmt.where(AgentMemory.symbol == symbol)
        if correlation_id is not None:
            stmt = stmt.where(AgentMemory.correlation_id == correlation_id)

        stmt = (
            stmt.order_by(AgentMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_by_type(
        self,
        *,
        agent_id: str | None = None,
    ) -> dict[str, int]:
        stmt = select(
            AgentMemory.memory_type,
            func.count(AgentMemory.id),
        ).group_by(AgentMemory.memory_type)

        if agent_id is not None:
            stmt = stmt.where(AgentMemory.agent_id == agent_id)

        rows = self.db.execute(stmt).all()
        return {str(memory_type): int(count) for memory_type, count in rows}
