from fastapi import APIRouter

from app.market.adapter import market

router = APIRouter(
    prefix="/market",
    tags=["Market"],
)


@router.get("/symbols")
def symbols():
    return market.symbols()


@router.get("/tick/{symbol}")
def tick(symbol: str):
    return market.tick(symbol)


@router.get("/candles/{symbol}")
def candles(
    symbol: str,
    timeframe: str = "M1",
    count: int = 500,
):
    return market.candles(symbol, timeframe, count)