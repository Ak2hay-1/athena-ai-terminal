from app.market.candles import candles
from app.market.symbols import all_symbols
from app.market.symbols import symbol_exists
from app.market.ticks import latest_tick


class MarketAdapter:

    def symbols(self):
        return all_symbols()

    def exists(self, symbol):
        return symbol_exists(symbol)

    def tick(self, symbol):
        return latest_tick(symbol)

    def candles(self, symbol, timeframe, count):
        return candles(symbol, timeframe, count)


market = MarketAdapter()