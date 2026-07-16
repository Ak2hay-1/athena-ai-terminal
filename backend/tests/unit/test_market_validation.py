import pytest

from app.core.exceptions import ValidationException
from app.core.market_validation import validate_symbol
from app.core.market_validation import validate_timeframe


def test_validate_symbol_ok():
    assert validate_symbol("eurusd") == "EURUSD"


def test_validate_symbol_invalid():
    with pytest.raises(ValidationException):
        validate_symbol("INVALID")


def test_validate_timeframe_ok():
    assert validate_timeframe("m15") == "M15"
