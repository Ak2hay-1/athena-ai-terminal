from app.mt5.sdk import mt5
import pandas as pd

from app.market.client import client
from app.market.timeframes import TIMEFRAMES


def candles(symbol: str, timeframe: str, count: int = 500):

    client.connect()

    rates = mt5.copy_rates_from_pos(
        symbol,
        TIMEFRAMES[timeframe],
        0,
        count,
    )

    if rates is None:
        return []

    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(df["time"], unit="s")

    return df.to_dict(orient="records")