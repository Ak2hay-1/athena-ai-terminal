"""
Trading journal API.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database.database import get_db
from app.models.journal_entry import JournalEntry
from app.models.user import User
from app.repositories.journal_repository import JournalRepository

router = APIRouter(
    prefix="/journal",
    tags=["Journal"],
)

ALLOWED_ENTRY_TYPES = {
    "note",
    "trade_review",
    "recommendation_review",
    "auto_close",
}


class JournalCreate(BaseModel):
    entry_type: str = Field(default="note", examples=["note"])
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(default="")
    symbol: str | None = Field(default=None, max_length=16)
    tags: list[str] = Field(default_factory=list)
    recommendation_id: int | None = None
    paper_position_id: int | None = None


class JournalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    tags: list[str] | None = None
    symbol: str | None = Field(default=None, max_length=16)
    entry_type: str | None = None


class JournalRead(BaseModel):
    id: int
    entry_type: str
    title: str
    body: str
    symbol: str | None = None
    tags: list = Field(default_factory=list)
    recommendation_id: int | None = None
    paper_position_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


def _normalize_entry_type(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in ALLOWED_ENTRY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"entry_type must be one of: {', '.join(sorted(ALLOWED_ENTRY_TYPES))}",
        )
    return normalized


@router.get("", response_model=list[JournalRead])
def list_journal(
    symbol: str | None = Query(default=None),
    entry_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[JournalRead]:
    repo = JournalRepository(db)
    normalized_type = _normalize_entry_type(entry_type) if entry_type else None
    rows = repo.list_for_user(
        current_user.id,
        symbol=symbol.upper() if symbol else None,
        entry_type=normalized_type,
        limit=limit,
    )
    return [JournalRead.model_validate(r) for r in rows]


@router.post("", response_model=JournalRead, status_code=status.HTTP_201_CREATED)
def create_journal(
    payload: JournalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JournalRead:
    repo = JournalRepository(db)
    entry = JournalEntry(
        user_id=current_user.id,
        entry_type=_normalize_entry_type(payload.entry_type),
        title=payload.title.strip(),
        body=payload.body or "",
        symbol=payload.symbol.upper() if payload.symbol else None,
        tags=list(payload.tags or []),
        recommendation_id=payload.recommendation_id,
        paper_position_id=payload.paper_position_id,
    )
    repo.create(entry)
    db.commit()
    db.refresh(entry)
    return JournalRead.model_validate(entry)


@router.patch("/{entry_id}", response_model=JournalRead)
def update_journal(
    entry_id: int,
    payload: JournalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> JournalRead:
    repo = JournalRepository(db)
    entry = repo.get_for_user(entry_id, current_user.id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    values: dict = {}
    if payload.title is not None:
        values["title"] = payload.title.strip()
    if payload.body is not None:
        values["body"] = payload.body
    if payload.tags is not None:
        values["tags"] = list(payload.tags)
    if payload.symbol is not None:
        values["symbol"] = payload.symbol.upper() if payload.symbol else None
    if payload.entry_type is not None:
        values["entry_type"] = _normalize_entry_type(payload.entry_type)

    if values:
        repo.update(entry, values)
        db.commit()
        db.refresh(entry)
    return JournalRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal(
    entry_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    repo = JournalRepository(db)
    entry = repo.get_for_user(entry_id, current_user.id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    repo.delete(entry)
    db.commit()
