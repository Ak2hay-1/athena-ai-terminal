import MetaTrader5 as mt5

from app.core.logger import logger


class MT5Client:

    def __init__(self):
        self.connected = False

    def connect(self):

        if mt5.initialize():

            self.connected = True

            logger.info("Connected to MetaTrader5")

            return True

        logger.error(mt5.last_error())

        return False

    def shutdown(self):

        mt5.shutdown()

        self.connected = False

    def symbols(self):

        return mt5.symbols_get()

    def symbol_info(self, symbol):

        return mt5.symbol_info(symbol)

    def tick(self, symbol):

        return mt5.symbol_info_tick(symbol)


mt5_client = MT5Client()