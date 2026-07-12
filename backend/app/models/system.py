from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.database.base import Base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class SystemInfo(Base):

    __tablename__ = "system_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    version: Mapped[str] = mapped_column(String(20))

    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now()
    )