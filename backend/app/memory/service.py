"""
Trading intelligence memory service.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.database.database import SessionLocal
from app.memory.repository import MemoryRepository
from app.models.agent_memory import AgentMemory

logger = get_logger("athena.memory")

VALID_MEMORY_TYPES = frozenset(
    {
        "observation",
        "decision",
        "trade_outcome",
        "statistic",
        "user_feedback",
        "reasoning",
    }
)


class MemoryService:
    """
    Store and query agent trading intelligence (not conversation memory).
    """

    def __init__(self, db: Session | None = None) -> None:
        self._external_db = db

    def store(
        self,
        *,
        agent_id: str,
        memory_type: str,
        payload: dict[str, Any],
        symbol: str | None = None,
        timeframe: str | None = None,
        correlation_id: str | None = None,
        meta: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> AgentMemory:
        if memory_type not in VALID_MEMORY_TYPES:
            raise ValueError(
                f"invalid memory_type={memory_type!r}; "
                f"expected one of {sorted(VALID_MEMORY_TYPES)}"
            )

        owns_session = self._external_db is None
        db = self._external_db or SessionLocal()
        try:
            repo = MemoryRepository(db)
            record = AgentMemory(
                agent_id=agent_id,
                memory_type=memory_type,
                symbol=symbol,
                timeframe=timeframe,
                correlation_id=correlation_id,
                payload=payload,
                meta=meta,
                notes=notes,
            )
            repo.create(record)
            db.commit()
            db.refresh(record)
            logger.info(
                "memory action=store agent=%s type=%s id=%s",
                agent_id,
                memory_type,
                record.id,
            )
            return record
        except Exception:
            db.rollback()
            logger.exception(
                "memory action=store agent=%s type=%s status=error",
                agent_id,
                memory_type,
            )
            raise
        finally:
            if owns_session:
                db.close()

    def query(
        self,
        *,
        agent_id: str | None = None,
        memory_type: str | None = None,
        symbol: str | None = None,
        correlation_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentMemory]:
        owns_session = self._external_db is None
        db = self._external_db or SessionLocal()
        try:
            repo = MemoryRepository(db)
            return repo.query(
                agent_id=agent_id,
                memory_type=memory_type,
                symbol=symbol,
                correlation_id=correlation_id,
                limit=limit,
            )
        finally:
            if owns_session:
                db.close()

    def stats(
        self,
        *,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        owns_session = self._external_db is None
        db = self._external_db or SessionLocal()
        try:
            repo = MemoryRepository(db)
            by_type = repo.count_by_type(agent_id=agent_id)
            return {
                "agent_id": agent_id,
                "by_type": by_type,
                "total": sum(by_type.values()),
            }
        finally:
            if owns_session:
                db.close()
