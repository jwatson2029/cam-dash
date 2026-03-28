"""
Logging configuration for LaViewNVR.

Uses loguru for structured, rotating daily logs.
Falls back to standard logging if loguru is unavailable.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    from loguru import logger as _loguru_logger

    _USE_LOGURU = True
except ImportError:
    _USE_LOGURU = False


def setup_logging(log_path: str = "logs/nvr.log", log_level: str = "INFO") -> None:
    """Configure application-wide logging to file and stdout."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    if _USE_LOGURU:
        _loguru_logger.remove()
        _loguru_logger.add(sys.stdout, level=log_level, colorize=True,
                           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
        _loguru_logger.add(log_path, level=log_level, rotation="00:00",
                           retention="30 days", compression="gz",
                           format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}")
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format=fmt,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.TimedRotatingFileHandler(
                    log_path, when="midnight", backupCount=30
                ),
            ],
        )
