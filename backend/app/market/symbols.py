from app.mt5.sdk import mt5

from app.market.client import client


def all_symbols():

    client.connect()

    symbols = mt5.symbols_get()

    return [s.name for s in symbols]


def symbol_exists(symbol: str):

    client.connect()

    return mt5.symbol_info(symbol) is not None