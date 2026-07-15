"""
MetaTrader 5 Providers.

Centralized dependency providers for the MT5 module.
"""

from __future__ import annotations

from app.mt5.connection import MT5Connection
from app.mt5.manager import MT5Manager

# ==========================================================
# Shared Instances
# ==========================================================

connection = MT5Connection()

manager = MT5Manager(
    connection=connection,
)


# ==========================================================
# Dependency Providers
# ==========================================================

def get_mt5_connection() -> MT5Connection:
    """
    Return the shared MT5 connection instance.
    """

    return connection


def get_mt5_manager() -> MT5Manager:
    """
    Return the shared MT5 manager instance.
    """

    return manager