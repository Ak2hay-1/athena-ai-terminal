"""Candle engine: OHLC construction and time-based closing."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

from app.marketdata.engine import CandleBuilder
from app.marketdata.engine import CandleEngine
from app.marketdata.engine import EngineCallbacks
from app.marketdata.ticks import Tick


def _msc(y, mo, d, h, mi, s=0, ms=0) -> int:
    return (
        int(datetime(y, mo, d, h, mi, s, tzinfo=UTC).timestamp()) * 1000 + ms
    )


def _tick(time_msc: int, bid: float, ask: float | None = None) -> Tick:
    return Tick(
        symbol="XAUUSD",
        time_msc=time_msc,
        bid=bid,
        ask=ask if ask is not None else bid + 0.2,
    )


class TestCandleBuilder:
    def test_first_tick_initializes_ohlc(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 0), 2400.0))

        candle = builder.current
        assert candle is not None
        assert candle.open == 2400.0
        assert candle.high == 2400.0
        assert candle.low == 2400.0
        assert candle.close == 2400.0
        assert candle.bucket_start == _msc(2026, 7, 21, 10, 20, 0) // 1000

    def test_open_never_changes(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 0), 2400.0))
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 15), 2405.0))
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2395.0))

        candle = builder.current
        assert candle.open == 2400.0
        assert candle.high == 2405.0
        assert candle.low == 2395.0
        assert candle.close == 2395.0

    def test_boundary_closes_candle(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 59), 2400.0))
        closed = builder.apply_tick(
            _tick(_msc(2026, 7, 21, 10, 21, 0), 2401.0)
        )

        assert closed is not None
        assert closed.complete is True
        assert closed.close == 2400.0
        assert builder.current.open == 2401.0
        assert builder.current.bucket_start == closed.bucket_start + 60

    def test_gap_never_merges_into_oversized_candle(self):
        """A 3-minute tick gap must not stretch the old candle."""

        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 10), 2400.0))
        closed = builder.apply_tick(
            _tick(_msc(2026, 7, 21, 10, 24, 5), 2450.0)
        )

        assert closed is not None
        # Closed candle keeps its own bucket's range only.
        assert closed.high == 2400.0
        assert closed.low == 2400.0
        # New candle opens in its own bucket at the new price.
        assert builder.current.bucket_start == (
            _msc(2026, 7, 21, 10, 24, 0) // 1000
        )
        assert builder.current.open == 2450.0

    def test_stale_tick_cannot_reopen_closed_bucket(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 10), 2400.0))
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 21, 10), 2401.0))

        stale = builder.apply_tick(
            _tick(_msc(2026, 7, 21, 10, 20, 30), 2500.0)
        )
        assert stale is None
        assert builder.current.high == 2401.0  # unaffected

    def test_out_of_order_tick_within_bucket_keeps_close(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2400.0))
        builder.apply_tick(
            _tick(_msc(2026, 7, 21, 10, 20, 10), 2410.0)
        )  # late tick

        candle = builder.current
        assert candle.high == 2410.0  # extends range
        assert candle.close == 2400.0  # close not stepped backwards

    def test_seed_floor_blocks_historical_buckets(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.seed(_msc(2026, 7, 21, 10, 20, 0) // 1000)

        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2400.0))
        assert builder.current is None  # bucket already completed in DB

        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 21, 5), 2401.0))
        assert builder.current is not None

    def test_close_expired_by_time(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2400.0))

        # Bucket ends at 10:21:00 broker time.
        before = builder.close_expired(
            _msc(2026, 7, 21, 10, 20, 59) / 1000.0
        )
        assert before is None

        closed = builder.close_expired(
            _msc(2026, 7, 21, 10, 21, 0) / 1000.0
        )
        assert closed is not None
        assert closed.complete is True
        assert builder.current is None

    def test_first_candle_after_start_is_partial(self):
        builder = CandleBuilder("XAUUSD", "M1")
        builder.apply_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2400.0))
        assert builder.current.partial is True

        closed = builder.apply_tick(
            _tick(_msc(2026, 7, 21, 10, 21, 0), 2401.0)
        )
        assert closed.partial is True
        assert builder.current.partial is False  # full bucket coverage


class TestCandleEngine:
    def test_multi_timeframe_close(self):
        closed: list = []
        engine = CandleEngine(
            timeframes=["M1", "M5"],
            callbacks=EngineCallbacks(on_candle_closed=closed.append),
        )

        engine.process_tick(_tick(_msc(2026, 7, 21, 10, 24, 30), 2400.0))
        engine.process_tick(_tick(_msc(2026, 7, 21, 10, 25, 0), 2401.0))

        # Crossing 10:25 closes both the M1 and the M5 bucket.
        assert sorted(c.timeframe for c in closed) == ["M1", "M5"]
        assert all(c.complete for c in closed)

    def test_symbols_are_isolated(self):
        engine = CandleEngine(timeframes=["M1"])
        engine.process_tick(_tick(_msc(2026, 7, 21, 10, 20, 5), 2400.0))
        eur = Tick(
            symbol="EURUSD",
            time_msc=_msc(2026, 7, 21, 10, 20, 6),
            bid=1.09,
            ask=1.0902,
        )
        engine.process_tick(eur)

        assert engine.current_candle("XAUUSD", "M1").close == 2400.0
        assert engine.current_candle("EURUSD", "M1").close == 1.09

    def test_restart_scenario_no_oversized_candle(self):
        """
        Simulated restart: engine seeded from DB, first live tick far
        ahead of stored history. The new forming candle must belong to
        the tick's own bucket, not span the gap.
        """

        engine = CandleEngine(timeframes=["M1"])
        # DB says newest completed candle opened at 08:00.
        engine.seed_last_completed(
            "XAUUSD", "M1", _msc(2026, 7, 21, 8, 0, 0) // 1000
        )

        engine.process_tick(_tick(_msc(2026, 7, 21, 10, 20, 30), 2450.0))
        forming = engine.current_candle("XAUUSD", "M1")

        assert forming.bucket_start == _msc(2026, 7, 21, 10, 20, 0) // 1000
        assert forming.open == 2450.0
        assert forming.high == 2450.0
        assert forming.low == 2450.0

    def test_metrics(self):
        engine = CandleEngine(timeframes=["M1"])
        engine.process_tick(_tick(_msc(2026, 7, 21, 10, 20, 5), 2400.0))
        metrics = engine.metrics()
        assert metrics["ticks_processed"] == 1
        assert metrics["symbols"] == 1
