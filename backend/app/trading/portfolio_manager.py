"""
Athena Portfolio Manager.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.trading.trade_journal import trade_journal


@dataclass(slots=True)
class PortfolioSnapshot:

    balance: float = 10000.0

    equity: float = 10000.0

    margin: float = 0.0

    free_margin: float = 10000.0

    floating_profit: float = 0.0

    closed_profit: float = 0.0

    drawdown: float = 0.0

    daily_profit: float = 0.0

    weekly_profit: float = 0.0

    monthly_profit: float = 0.0

    exposure: dict[str, float] = field(
        default_factory=dict,
    )

    updated_at: datetime = field(
        default_factory=datetime.utcnow,
    )


class PortfolioManager:
    """
    Portfolio state manager.
    """

    def __init__(self):

        self.snapshot = PortfolioSnapshot()

    # -------------------------------------------------

    def update_closed_profit(self):

        self.snapshot.closed_profit = (
            trade_journal.net_profit()
        )

        self.snapshot.balance = (
            10000.0 +
            self.snapshot.closed_profit
        )

    # -------------------------------------------------

    def update_equity(
        self,
        floating_profit: float,
    ):

        self.snapshot.floating_profit = (
            floating_profit
        )

        self.snapshot.equity = (

            self.snapshot.balance +

            floating_profit

        )

        self.snapshot.free_margin = (

            self.snapshot.equity -

            self.snapshot.margin

        )

        self.snapshot.updated_at = (
            datetime.utcnow()
        )

    # -------------------------------------------------

    def update_drawdown(self):

        peak = max(
            10000.0,
            self.snapshot.balance,
        )

        if peak == 0:

            self.snapshot.drawdown = 0

            return

        self.snapshot.drawdown = round(

            (

                peak -

                self.snapshot.equity

            )

            / peak

            * 100,

            2,

        )

    # -------------------------------------------------

    def add_exposure(

        self,

        symbol: str,

        volume: float,

    ):

        self.snapshot.exposure.setdefault(

            symbol,

            0,

        )

        self.snapshot.exposure[symbol] += volume

    # -------------------------------------------------

    def remove_exposure(

        self,

        symbol: str,

        volume: float,

    ):

        if symbol not in self.snapshot.exposure:

            return

        self.snapshot.exposure[symbol] -= volume

        if self.snapshot.exposure[symbol] <= 0:

            del self.snapshot.exposure[symbol]

    # -------------------------------------------------

    def summary(self):

        self.update_closed_profit()

        self.update_drawdown()

        return {

            "balance": self.snapshot.balance,

            "equity": self.snapshot.equity,

            "floating_profit": self.snapshot.floating_profit,

            "closed_profit": self.snapshot.closed_profit,

            "drawdown": self.snapshot.drawdown,

            "free_margin": self.snapshot.free_margin,

            "exposure": self.snapshot.exposure,

        }


portfolio_manager = PortfolioManager()