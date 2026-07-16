"""
Market symbol and timeframe validation.
"""

from __future__ import annotations

from app.core.constants import SUPPORTED_SYMBOLS
from app.core.constants import SUPPORTED_TIMEFRAMES
from app.core.exceptions import ValidationException


def validate_symbol(symbol: str) -> str:
    normalized = symbol.upper().strip()

    if normalized not in SUPPORTED_SYMBOLS:
        raise ValidationException(
            f"Unsupported symbol: {symbol}"
        )

    return normalized


def validate_timeframe(timeframe: str) -> str:
    normalized = timeframe.upper().strip()

    if normalized not in SUPPORTED_TIMEFRAMES:
        raise ValidationException(
            f"Unsupported timeframe: {timeframe}"
        )

    return normalized
