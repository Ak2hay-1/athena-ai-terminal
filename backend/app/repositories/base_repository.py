"""
Base Repository.

Generic SQLAlchemy repository.
"""

from __future__ import annotations

from typing import Generic
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository.

    Transaction management is handled by the service layer.
    """

    def __init__(
        self,
        db: Session,
        model: type[ModelType],
    ) -> None:

        self.db = db
        self.model = model

    # ======================================================
    # Create
    # ======================================================

    def create(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.db.add(obj)

        return obj

    # ======================================================
    # Read
    # ======================================================

    def get_by_id(
        self,
        obj_id: int,
    ) -> ModelType | None:

        return self.db.get(
            self.model,
            obj_id,
        )

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:

        stmt = (

            select(self.model)

            .offset(skip)

            .limit(limit)

        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ======================================================
    # Update
    # ======================================================

    def update(
        self,
        obj: ModelType,
        values: dict,
    ) -> ModelType:

        for field, value in values.items():

            setattr(
                obj,
                field,
                value,
            )

        return obj

    # ======================================================
    # Delete
    # ======================================================

    def delete(
        self,
        obj: ModelType,
    ) -> None:

        self.db.delete(obj)

    # ======================================================
    # Exists
    # ======================================================

    def exists(
        self,
        obj_id: int,
    ) -> bool:

        return self.get_by_id(
            obj_id,
        ) is not None

    # ======================================================
    # Refresh
    # ======================================================

    def refresh(
        self,
        obj: ModelType,
    ) -> None:

        self.db.refresh(obj)

    # ======================================================
    # Flush
    # ======================================================

    def flush(self) -> None:

        self.db.flush()