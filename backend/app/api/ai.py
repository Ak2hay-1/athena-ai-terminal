"""
AI API.
"""

from __future__ import annotations

import traceback

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.recommendation_engine import recommendation_engine
from app.database.session import get_db
from app.services.market_service import MarketService

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


@router.post("/analyze/{symbol}")
def analyze(
    symbol: str,
    timeframe: str = "M1",
    limit: int = 500,
    db: Session = Depends(get_db),
):
    try:

        service = MarketService(db)

        candles = service.latest(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if not candles:
            return {
                "success": False,
                "message": "No candle data found."
            }

        dataframe = pd.DataFrame(
            [candle.to_dict() for candle in candles]
        )

        recommendation = recommendation_engine.analyze(
            dataframe
        )

        return {
            "success": True,
            "recommendation": recommendation.model_dump(),
        }

    except Exception:
        return {
            "success": False,
            "traceback": traceback.format_exc(),
        }