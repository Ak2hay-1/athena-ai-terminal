"""
Athena Performance Tracker.
"""

from __future__ import annotations

import math

from app.trading.trade_journal import trade_journal


class PerformanceTracker:
    """
    Calculates trading performance statistics.
    """

    def _profits(self):

        return [

            trade.profit

            for trade in trade_journal.trades()

        ]

    # -------------------------------------------------

    def expectancy(self):

        profits = self._profits()

        if not profits:

            return 0

        wins = [

            p

            for p in profits

            if p > 0

        ]

        losses = [

            p

            for p in profits

            if p <= 0

        ]

        win_rate = len(wins) / len(profits)

        avg_win = (

            sum(wins) / len(wins)

            if wins

            else 0

        )

        avg_loss = (

            abs(sum(losses) / len(losses))

            if losses

            else 0

        )

        return round(

            (

                win_rate * avg_win

            )

            -

            (

                (1 - win_rate)

                * avg_loss

            ),

            2,

        )

    # -------------------------------------------------

    def profit_factor(self):

        profits = self._profits()

        gross_profit = sum(

            p

            for p in profits

            if p > 0

        )

        gross_loss = abs(

            sum(

                p

                for p in profits

                if p < 0

            )

        )

        if gross_loss == 0:

            return float("inf")

        return round(

            gross_profit /

            gross_loss,

            2,

        )

    # -------------------------------------------------

    def sharpe_ratio(self):

        profits = self._profits()

        if len(profits) < 2:

            return 0

        avg = sum(profits) / len(profits)

        variance = sum(

            (

                x - avg

            ) ** 2

            for x in profits

        ) / (len(profits) - 1)

        std = math.sqrt(

            variance

        )

        if std == 0:

            return 0

        return round(

            avg / std,

            2,

        )

    # -------------------------------------------------

    def summary(self):

        return {

            "expectancy": self.expectancy(),

            "profit_factor": self.profit_factor(),

            "sharpe_ratio": self.sharpe_ratio(),

            "journal": trade_journal.statistics(),

        }


performance_tracker = PerformanceTracker()