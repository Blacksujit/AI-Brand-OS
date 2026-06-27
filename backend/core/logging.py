from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger as _base_logger

from core.config import Settings


class JsonSink:
    def __init__(self, *, colorize: bool = False) -> None:
        self._colorize = colorize

    def __call__(self, message) -> None:  # type: ignore[no-untyped-def]
        record = message.record
        raw = record["time"]
        timestamp = raw.astimezone(UTC) if hasattr(raw, "astimezone") else datetime.fromtimestamp(raw, tz=UTC)

        entry: dict[str, Any] = {
            "timestamp": timestamp.isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
        }

        if record.get("exception"):
            entry["exception"] = str(record["exception"])

        extra = record.get("extra", {})
        if extra:
            entry["extra"] = extra

        sys.stdout.write(json.dumps(entry, default=str) + "\n")
        sys.stdout.flush()


def configure_logging(settings: Settings) -> None:
    _base_logger.remove()

    level = settings.log_level.upper()

    if settings.log_json:
        _base_logger.add(
            JsonSink(),
            level=level,
        )
    else:
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
            colorize=True,
            backtrace=settings.is_development,
            diagnose=settings.is_development,
        )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    _base_logger.add(
        str(log_dir / "brandos.log"),
        rotation="10 MB",
        retention="30 days",
        level="WARNING",
        format="{time} | {level} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=settings.is_development,
    )
    _base_logger.add(
        str(log_dir / "debug.log"),
        rotation="50 MB",
        retention="7 days",
        level="DEBUG",
        format="{time} | {level} | {name}:{function}:{line} | {message}",
        backtrace=True,
        diagnose=settings.is_development,
    )


def get_logger(name: str | None = None) -> type[_base_logger.__class__]:
    return _base_logger
