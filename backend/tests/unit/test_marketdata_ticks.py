"""Normalized tick behaviour."""

from __future__ import annotations

from app.marketdata.ticks import Tick


class TestTick:
    def test_mid_and_spread(self):
        tick = Tick(symbol="EURUSD", time_msc=1_000, bid=1.0900, ask=1.0902)
        assert tick.mid == (1.0900 + 1.0902) / 2
        assert round(tick.spread, 6) == 0.0002

    def test_price_prefers_bid(self):
        tick = Tick(
            symbol="EURUSD",
            time_msc=1_000,
            bid=1.09,
            ask=1.0902,
            last=1.0950,
        )
        assert tick.price == 1.09

    def test_price_falls_back_to_last_then_ask(self):
        no_bid = Tick(
            symbol="US30", time_msc=1_000, bid=0.0, ask=0.0, last=39000.0
        )
        assert no_bid.price == 39000.0

        ask_only = Tick(symbol="US30", time_msc=1_000, bid=0.0, ask=39001.0)
        assert ask_only.price == 39001.0

    def test_epoch_seconds(self):
        tick = Tick(
            symbol="EURUSD", time_msc=1_752_000_000_500, bid=1.0, ask=1.0002
        )
        assert tick.epoch_seconds == 1_752_000_000.5
