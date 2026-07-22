"""
Normalized market tick.

All timestamps are broker/server time (epoch milliseconds) as reported
by MT5 — local machine time is never used for candle bucketing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Tick:
    """A single normalized market tick."""

    symbol: str
    # Broker/server time in epoch milliseconds.
    time_msc: int
    bid: float
    ask: float
    last: float = 0.0

    @property
    def epoch_seconds(self) -> float:
        return self.time_msc / 1000.0

    @property
    def mid(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2.0
        return self.bid or self.ask or self.last

    @property
    def spread(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return 0.0

    @property
    def price(self) -> float:
        """
        Candle price for OHLC construction.

        MT5 builds bars from bid prices, so bid keeps tick-built candles
        consistent with broker history. Falls back to last/mid for
        instruments without a bid stream.
        """

        if self.bid > 0:
            return self.bid
        if self.last > 0:
            return self.last
        return self.mid
