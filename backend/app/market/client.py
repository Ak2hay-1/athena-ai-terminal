import MetaTrader5 as mt5

from app.core.logger import logger


class MT5Client:

    def __init__(self):
        self.connected = False

    def connect(self):

        if self.connected:
            return True

        if mt5.initialize():
            self.connected = True
            logger.info("Connected to MT5")
            return True

        logger.error(mt5.last_error())
        return False

    def shutdown(self):
        mt5.shutdown()
        self.connected = False


client = MT5Client()