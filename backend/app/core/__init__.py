"""
Athena Core Package.
"""

from app.core.logger import get_logger
from app.core.logger import logger
from app.core.settings import settings

__all__ = [
    "settings",
    "logger",
    "get_logger",
]
