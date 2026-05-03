from __future__ import annotations

import logging
import os
import sys

import structlog
from structlog.types import Processor

_configured: bool = False


def is_production() -> bool:
    """Return True when running on Render or when LOG_FORMAT=json is explicitly set."""
    return (
        os.environ.get("RENDER", "").lower() == "true"
        or os.environ.get("LOG_FORMAT", "").lower() == "json"
    )


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog and the stdlib root logger.

    Idempotent — safe to call multiple times; only the first call takes effect.
    Dev mode renders colorized human-readable output; production emits JSON.
    Uses stdlib.LoggerFactory so structlog output is capturable by pytest caplog.
    """
    global _configured
    if _configured:
        return

    log_level_int: int = getattr(logging, log_level.upper(), logging.INFO)

    renderer: Processor = (
        structlog.processors.JSONRenderer() if is_production() else structlog.dev.ConsoleRenderer()
    )

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        renderer,
    ]

    # cache_logger_on_first_use=False is required for structlog.testing.capture_logs()
    # to intercept log calls in tests; the performance overhead is negligible.
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    # Pass-through formatter: structlog already rendered the string, so the stdlib
    # handler just emits it as-is without adding its own timestamp/level prefix.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level_int)

    # Our middleware handles request logging; suppress uvicorn's duplicate access log.
    logging.getLogger("uvicorn.access").propagate = False

    _configured = True
