"""
Athena Logger.

Provides a centralized logger for the application.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.settings import settings

# ==========================================================
# Configuration
# ==========================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

log_file = Path(settings.LOG_FILE)
log_file.parent.mkdir(parents=True, exist_ok=True)

formatter = logging.Formatter(
    fmt=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=10 * 1024 * 1024,
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(formatter)


# ==========================================================
# Logger Factory
# ==========================================================

_configured = False


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger.
    """

    global _configured

    logger = logging.getLogger(name)

    if not _configured:
        logger.setLevel(
            getattr(
                logging,
                settings.LOG_LEVEL.upper(),
                logging.INFO,
            )
        )

        if not logger.handlers:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        logger.propagate = False

        logging.getLogger("sqlalchemy.engine").setLevel(
            logging.WARNING
        )

        logging.getLogger("sqlalchemy.pool").setLevel(
            logging.WARNING
        )

        logging.getLogger("uvicorn.access").setLevel(
            logging.INFO
        )

        logging.getLogger("uvicorn.error").setLevel(
            logging.INFO
        )

        _configured = True

    return logger


# Default application logger
logger = get_logger("athena")
