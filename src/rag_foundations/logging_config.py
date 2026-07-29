"""Minimal standard-library logging configuration."""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "rag_foundations"
HANDLER_MARKER = "_rag_foundations_project_handler"


def configure_logging(level: str = "INFO") -> None:
    """Configure project logging explicitly.

    This function avoids logging settings objects or secret-bearing values.
    """

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(numeric_level)
    logger.propagate = False

    handler = next(
        (
            item
            for item in logger.handlers
            if getattr(item, HANDLER_MARKER, False)
        ),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)
        setattr(handler, HANDLER_MARKER, True)
        logger.addHandler(handler)
    else:
        handler.stream = sys.stderr
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
