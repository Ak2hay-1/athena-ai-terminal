"""
Athena Performance Metrics.
"""

from __future__ import annotations


class PerformanceMetrics:
    """
    Calculate trading performance metrics.
    """

    def calculate(
        self,
        trades: list[dict],
    ) -> dict:

        if not trades:

            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "net_profit": 0,
                "gross_profit": 0,
                "gross_loss": 0,
                "profit_factor": 0,
                "average_profit": 0,
            }

        profits = [
            trade["profit"]
            for trade in trades
        ]

        wins = [
            profit
            for profit in profits
            if profit > 0
        ]

        losses = [
            profit
            for profit in profits
            if profit <= 0
        ]

        gross_profit = sum(wins)

        gross_loss = abs(
            sum(losses)
        )

        total = len(trades)

        net_profit = sum(profits)

        win_rate = (
            len(wins) / total
        ) * 100

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else float("inf")
        )

        average_profit = (
            net_profit / total
        )

        return {

            "total_trades": total,

            "wins": len(wins),

            "losses": len(losses),

            "win_rate": round(
                win_rate,
                2,
            ),

            "net_profit": round(
                net_profit,
                2,
            ),

            "gross_profit": round(
                gross_profit,
                2,
            ),

            "gross_loss": round(
                gross_loss,
                2,
            ),

            "profit_factor": round(
                profit_factor,
                2,
            ),

            "average_profit": round(
                average_profit,
                2,
            ),

        }