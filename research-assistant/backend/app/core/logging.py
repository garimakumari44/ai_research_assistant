
from __future__ import annotations

import logging
import sys

from app.core.config import settings


# =============================================================================
# Module-level application logger
# =============================================================================

logger = logging.getLogger("app")


# =============================================================================
# Logging configuration
# =============================================================================

def setup_logging() -> None:
    """
    Configure application-wide logging.
    """

    log_level = getattr(
        logging,
        settings.LOG_LEVEL.upper(),
        logging.INFO,
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    root_logger.setLevel(log_level)

    # Prevent duplicate handlers when application reloads.
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    # Keep noisy libraries under control.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG
        if settings.DB_ECHO
        else logging.WARNING
    )


# =============================================================================
# Logger factory
# =============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Return a named application logger.
    """

    return logging.getLogger(name)


__all__ = [
    "logger",
    "setup_logging",
    "get_logger",
]

