"""
Athena Trade Simulation Engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


@dataclass(slots=True)
class SimulatedTrade:

    ticket: int

    symbol: str

    signal: str

    volume: float

    entry: float

    stop_loss: float

    take_profit: float

    open_time: str

    close_time: str | None = None

    close_price: float | None = None

    profit: float = 0

    status: TradeStatus = TradeStatus.OPEN


class SimulationEngine:

    def __init__(self):

        self.ticket = 1

    def open_trade(

        self,

        symbol: str,

        signal: str,

        volume: float,

        entry: float,

        stop_loss: float,

        take_profit: float,

        time: str,

    ) -> SimulatedTrade:

        trade = SimulatedTrade(

            ticket=self.ticket,

            symbol=symbol,

            signal=signal,

            volume=volume,

            entry=entry,

            stop_loss=stop_loss,

            take_profit=take_profit,

            open_time=time,

        )

        self.ticket += 1

        return trade

    def update(

        self,

        trade: SimulatedTrade,

        candle,

        time: str,

    ) -> SimulatedTrade:

        high = candle["high"]

        low = candle["low"]

        # BUY

        if trade.signal == "BUY":

            if low <= trade.stop_loss:

                trade.status = TradeStatus.STOP_LOSS

                trade.close_price = trade.stop_loss

            elif high >= trade.take_profit:

                trade.status = TradeStatus.TAKE_PROFIT

                trade.close_price = trade.take_profit

        # SELL

        else:

            if high >= trade.stop_loss:

                trade.status = TradeStatus.STOP_LOSS

                trade.close_price = trade.stop_loss

            elif low <= trade.take_profit:

                trade.status = TradeStatus.TAKE_PROFIT

                trade.close_price = trade.take_profit

        if trade.status != TradeStatus.OPEN:

            trade.close_time = time

            if trade.signal == "BUY":

                trade.profit = (

                    trade.close_price -

                    trade.entry

                ) * trade.volume

            else:

                trade.profit = (

                    trade.entry -

                    trade.close_price

                ) * trade.volume

        return trade


simulation_engine = SimulationEngine()