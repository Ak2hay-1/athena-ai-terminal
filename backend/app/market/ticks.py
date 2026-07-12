import MetaTrader5 as mt5

from app.market.client import client


def latest_tick(symbol: str):

    client.connect()

    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        return None

    return tick._asdict()