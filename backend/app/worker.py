from __future__ import annotations

import asyncio
import signal
import sys

from app.core.cache import get_cache
from app.core.config import get_settings
from app.core.db import get_db
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

RUNNING = True


def handle_shutdown(signum: int, frame) -> None:  # type: ignore[no-untyped-def]
    global RUNNING
    RUNNING = False
    logger.info("worker_shutdown_signal", signal=signum)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings)

    db = get_db(settings)
    cache = get_cache(settings)

    await db.initialize()
    await cache.initialize()

    logger.info("worker_started", poll_interval=5)

    while RUNNING:
        await asyncio.sleep(5)

    await cache.close()
    await db.close()
    logger.info("worker_stopped")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("worker_interrupted")
        sys.exit(0)
