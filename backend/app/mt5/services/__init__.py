"""
Athena MetaTrader 5 Module.

Public exports for the MT5 infrastructure.
"""

from app.mt5.providers import (
    connection,
    manager,
    get_mt5_connection,
    get_mt5_manager,
)

from app.mt5.connection import MT5Connection
from app.mt5.manager import MT5Manager

__all__ = [
    "MT5Connection",
    "MT5Manager",
    "connection",
    "manager",
    "get_mt5_connection",
    "get_mt5_manager",
]
