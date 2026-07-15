"""
Athena Risk Engine.

Calculates trade levels based on ATR and configurable
risk/reward ratios.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TradeLevels:
    """
    Calculated trade levels.
    """

    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float


class RiskEngine:
    """
    Calculate SL/TP using ATR.
    """

    ATR_MULTIPLIER = 1.5

    DEFAULT_RR = 2.0

    def calculate(
        self,
        direction: str,
        entry: float,
        atr: float,
        rr: float | None = None,
    ) -> TradeLevels:

        rr = rr or self.DEFAULT_RR

        risk = atr * self.ATR_MULTIPLIER

        direction = direction.upper()

        if direction == "BUY":

            stop_loss = entry - risk

            take_profit = entry + (risk * rr)

        elif direction == "SELL":

            stop_loss = entry + risk

            take_profit = entry - (risk * rr)

        else:

            stop_loss = entry

            take_profit = entry

            rr = 0.0

        return TradeLevels(
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward=round(rr, 2),
        )


risk_engine = RiskEngine()