"""Risk disclaimer acceptance schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class DisclaimerStatus(BaseModel):
    """Current risk disclaimer acceptance for the authenticated user."""

    accepted: bool
    accepted_at: datetime | None = None
    disclaimer_version: str | None = None
    app_version: str | None = None
    required_version: str

    model_config = {"from_attributes": True}


class DisclaimerAcceptRequest(BaseModel):
    """Client payload when accepting the risk disclaimer."""

    app_version: str = Field(..., min_length=1, max_length=32)
    disclaimer_version: str | None = Field(default=None, max_length=32)
