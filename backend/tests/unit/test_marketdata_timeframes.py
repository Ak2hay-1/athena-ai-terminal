"""Bucket math for the market data engine."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime

import pytest

from app.marketdata.timeframes import bucket_end_epoch
from app.marketdata.timeframes import bucket_start_datetime
from app.marketdata.timeframes import bucket_start_epoch
from app.marketdata.timeframes import is_same_bucket
from app.marketdata.timeframes import timeframe_seconds
from app.marketdata.timeframes import to_utc


def _epoch(y, mo, d, h, mi, s=0) -> int:
    return int(datetime(y, mo, d, h, mi, s, tzinfo=UTC).timestamp())


class TestBucketStart:
    def test_m1_mid_minute(self):
        moment = _epoch(2026, 7, 21, 10, 20, 15)
        assert bucket_start_epoch(moment, "M1") == _epoch(
            2026, 7, 21, 10, 20, 0
        )

    def test_m1_exact_boundary(self):
        moment = _epoch(2026, 7, 21, 10, 21, 0)
        assert bucket_start_epoch(moment, "M1") == moment

    def test_m5(self):
        moment = _epoch(2026, 7, 21, 10, 23, 59)
        assert bucket_start_epoch(moment, "M5") == _epoch(
            2026, 7, 21, 10, 20, 0
        )

    def test_h1(self):
        moment = _epoch(2026, 7, 21, 10, 59, 59)
        assert bucket_start_epoch(moment, "H1") == _epoch(
            2026, 7, 21, 10, 0, 0
        )

    def test_h4(self):
        moment = _epoch(2026, 7, 21, 15, 0, 1)
        assert bucket_start_epoch(moment, "H4") == _epoch(
            2026, 7, 21, 12, 0, 0
        )

    def test_d1(self):
        moment = _epoch(2026, 7, 21, 23, 59, 59)
        assert bucket_start_epoch(moment, "D1") == _epoch(
            2026, 7, 21, 0, 0, 0
        )

    def test_bucket_end_is_exclusive_next_open(self):
        moment = _epoch(2026, 7, 21, 10, 20, 30)
        assert bucket_end_epoch(moment, "M1") == _epoch(
            2026, 7, 21, 10, 21, 0
        )

    def test_unsupported_timeframe(self):
        with pytest.raises(ValueError):
            timeframe_seconds("M7")


class TestSameBucket:
    def test_same_minute(self):
        a = _epoch(2026, 7, 21, 10, 20, 0)
        b = _epoch(2026, 7, 21, 10, 20, 59)
        assert is_same_bucket(a, b, "M1")

    def test_adjacent_minutes(self):
        a = _epoch(2026, 7, 21, 10, 20, 59)
        b = _epoch(2026, 7, 21, 10, 21, 0)
        assert not is_same_bucket(a, b, "M1")


class TestDatetimeHelpers:
    def test_bucket_start_datetime(self):
        moment = datetime(2026, 7, 21, 10, 20, 45, tzinfo=UTC)
        result = bucket_start_datetime(moment, "M5")
        assert result == datetime(2026, 7, 21, 10, 20, 0, tzinfo=UTC)
        assert result.tzinfo is not None

    def test_to_utc_naive_treated_as_utc(self):
        naive = datetime(2026, 7, 21, 10, 20)
        aware = to_utc(naive)
        assert aware.tzinfo is UTC
        assert aware.hour == 10
