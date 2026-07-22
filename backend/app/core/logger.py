"""
Athena Logger.

Provides a centralized logger for the application.
"""

from __future__ import annotations

import logging
import os
import shutil
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


class SafeRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler that tolerates Windows file locks during rollover.

    On Windows, os.rename fails with WinError 32 when another process (e.g.
    uvicorn --reload parent, a second server instance, or a stale worker)
    still has the log file open. Fall back to copy + truncate so logging
    continues without emitting "--- Logging error ---" on every record.
    """

    def rotate(self, source: str, dest: str) -> None:
        try:
            super().rotate(source, dest)
        except PermissionError:
            if os.path.exists(dest):
                try:
                    os.remove(dest)
                except OSError:
                    pass
            shutil.copy2(source, dest)
            with open(source, "r+", encoding=self.encoding or "utf-8") as handle:
                handle.truncate(0)

    def doRollover(self) -> None:
        try:
            super().doRollover()
        except Exception:
            # Keep logging usable if rollover still fails (e.g. truncate blocked).
            if self.stream is None and not self.delay:
                self.stream = self._open()


formatter = logging.Formatter(
    fmt=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

file_handler = SafeRotatingFileHandler(
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
