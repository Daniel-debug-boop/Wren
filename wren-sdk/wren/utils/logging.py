"""Logging utilities for Wren SDK."""

from __future__ import annotations

import logging
import sys
from typing import Optional


def get_logger(
    name: str = 'wren',
    level: Optional[int] = None,
    format: str = '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name (default: "wren").
        level: Logging level (default: INFO).
        format: Log format string.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)

    # Only add handler if none exist (avoid duplicate logs)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(format))
        logger.addHandler(handler)
        logger.propagate = False

    return logger


class LoggerMixin:
    """Mixin that adds a self.log logger to any class."""

    @property
    def log(self) -> logging.Logger:
        """Get logger for this class."""
        cls = type(self)
        return get_logger(f'wren.{cls.__module__}.{cls.__qualname__}')
