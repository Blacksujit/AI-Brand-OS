from __future__ import annotations

import sys

from loguru import logger as _base_logger

from core.config import Settings


def configure_logging(settings: Settings) -> None:
    _base_logger.remove()
    level = settings.log_level.upper()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    _base_logger.add(
        sys.stdout,
        format=fmt,
        level=level,
        colorize=settings.is_development,
        backtrace=settings.is_development,
        diagnose=settings.is_development,
    )
    _base_logger.add(
        "logs/brandos.log",
        rotation="10 MB",
        retention="30 days",
        level="WARNING",
        format="{time} | {level} | {name}:{function}:{line} | {message}",
    )


def get_logger(name: str | None = None) -> type[_base_logger.__class__]:
    return _base_logger
