"""Confidence calibration bucket tests."""

from app.services.learning.metrics_utils import CONFIDENCE_BUCKETS
from app.services.learning.metrics_utils import win_rate


def test_confidence_buckets_cover_range():
    names = [b[0] for b in CONFIDENCE_BUCKETS]
    assert "70-80" in names
    assert "90-100" in names
    assert names[0] == "0-50"


def test_calibration_math_example():
    # Simulate 90-100 bucket with 91% actual
    labels = ["WIN"] * 91 + ["LOSS"] * 9
    assert win_rate(labels) == 91.0
