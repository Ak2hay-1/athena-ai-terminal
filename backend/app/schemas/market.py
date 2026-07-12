"""
Market response schemas.
"""

from datetime import datetime

from pydantic import BaseModel


class CandleResponse(BaseModel):
    symbol: str
    timeframe: str
    time: datetime

    open: float
    high: float
    low: float
    close: float

    tick_volume: int
    spread: int
    real_volume: int

    model_config = {
        "from_attributes": True
    }


class TickResponse(BaseModel):
    bid: float
    ask: float
    last: float | None = None
    volume: int | None = None
    time: int