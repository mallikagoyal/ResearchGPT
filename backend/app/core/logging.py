"""Application-wide logging configuration.

Call `configure_logging()` once at application startup. Every module should
then obtain a logger via `logging.getLogger(__name__)`.
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure root logging handlers and formatting.

    Uses a single stream handler to stdout so logs are captured correctly
    by Docker/container log drivers. Idempotent: safe to call more than
    once (e.g. in tests) without duplicating handlers.
    """
    settings = get_settings()
    root_logger = logging.getLogger()

    if root_logger.handlers:
        # Already configured (e.g. re-imported in tests/reloader).
        root_logger.setLevel(settings.LOG_LEVEL)
        return

    root_logger.setLevel(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
