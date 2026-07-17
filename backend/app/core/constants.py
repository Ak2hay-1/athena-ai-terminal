"""
Application constants.
"""

from __future__ import annotations

APP_AUTHOR = "Akshay Patil"

DEFAULT_SYMBOL = "XAUUSD"

SUPPORTED_SYMBOLS = [
    "XAUUSD",
    "XAGUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "USDCHF",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
    "BTCUSD",
    "ETHUSD",
    "SOLUSD",
]

SUPPORTED_TIMEFRAMES = [
    "M1",
    "M5",
    "M15",
    "M30",
    "H1",
    "H4",
    "D1",
]

DEFAULT_TIMEFRAME = "M5"

DEFAULT_CANDLE_LIMIT = 500

MAX_CANDLE_LIMIT = 5000

DEFAULT_LOT_SIZE = 0.01

MAX_RISK_PERCENT = 2.0

API_VERSION = "v1"

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)