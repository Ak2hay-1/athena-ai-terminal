"""
System Information Model.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel


class SystemInfo(BaseModel):
    """
    Stores Athena system metadata.
    """

    __tablename__ = "system_info"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SystemInfo("
            f"name='{self.name}', "
            f"version='{self.version}'"
            f")>"
        )
