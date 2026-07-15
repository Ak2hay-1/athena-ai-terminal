"""
Athena Trade Journal.
"""

from __future__ import annotations

from collections import deque

from app.trading.simulation_engine import (
    SimulatedTrade,
)


class TradeJournal:

    def __init__(

        self,

        max_history: int = 5000,

    ):

        self.history = deque(

            maxlen=max_history,

        )

    def add(

        self,

        trade: SimulatedTrade,

    ):

        self.history.append(

            trade,

        )

    def trades(self):

        return list(

            self.history,

        )

    def total(self):

        return len(

            self.history,

        )

    def wins(self):

        return len(

            [

                t

                for t in self.history

                if t.profit > 0

            ]

        )

    def losses(self):

        return len(

            [

                t

                for t in self.history

                if t.profit <= 0

            ]

        )

    def net_profit(self):

        return sum(

            t.profit

            for t in self.history

        )

    def statistics(self):

        total = self.total()

        wins = self.wins()

        losses = self.losses()

        return {

            "total_trades": total,

            "wins": wins,

            "losses": losses,

            "win_rate": (

                wins / total * 100

                if total

                else 0

            ),

            "net_profit": self.net_profit(),

        }


trade_journal = TradeJournal()