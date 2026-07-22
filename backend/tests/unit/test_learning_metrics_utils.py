"""Analytics metric helpers."""

from app.services.learning.metrics_utils import avg
from app.services.learning.metrics_utils import checklist_passed_names
from app.services.learning.metrics_utils import profit_factor


def test_profit_factor():
    assert profit_factor([2.0, -1.0, 1.0]) == 3.0


def test_avg_ignores_none():
    assert avg([1.0, None, 3.0]) == 2.0


def test_checklist_passed_names():
    names = checklist_passed_names(
        [
            {"name": "BOS", "passed": True},
            {"name": "FVG", "passed": False},
        ]
    )
    assert names == {"BOS"}
