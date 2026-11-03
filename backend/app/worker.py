"""Dedicated background worker consuming Redis email queues and maintaining media thumbnails.

Run with `python -m app.worker`. Keeps blocking SMTP TLS handshakes and retry backoffs out of
the HTTP uvicorn worker processes.
"""

import logging
import signal
import time

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings
from app.core.email import ConsoleEmailSender, EmailSender, RedisEmailQueue, SmtpEmailSender
from app.core.images import ensure_thumbnails
from app.core.observability import configure_logging

logger = logging.getLogger(__name__)


def build_worker_queue(settings: Settings | None = None) -> RedisEmailQueue:
    cfg = settings or get_settings()
    sender: EmailSender = SmtpEmailSender(cfg) if cfg.smtp_configured else ConsoleEmailSender()
    client = Redis.from_url(
        cfg.redis_url or "redis://localhost:6379/0",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=10,
    )
    return RedisEmailQueue(
        client,
        sender,
        prefix=cfg.redis_key_prefix,
        max_retries=cfg.smtp_max_retries,
        enqueue_only=False,
    )


def run_worker(*, max_cycles: int | None = None) -> int:
    settings = get_settings()
    configure_logging(settings)
    queue = build_worker_queue(settings)
    running = True

    def _stop(signum, _frame) -> None:
        nonlocal running
        logger.info("Worker received signal %s; shutting down gracefully", signum)
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    logger.info("Starting DaTeNO background worker (prefix=%s)", settings.redis_key_prefix)
    processed = 0
    cycles = 0
    last_thumbnail_sync = 0.0

    while running:
        now = time.monotonic()
        if now - last_thumbnail_sync >= 300.0:
            try:
                ensure_thumbnails(settings.media_dir / "products")
            except Exception:
                logger.warning("Periodic thumbnail check failed", exc_info=True)
            last_thumbnail_sync = now

        try:
            if queue.consume_one(timeout=2):
                processed += 1
        except RedisError:
            logger.warning("Redis connection error in worker; retrying in 2s", exc_info=True)
            time.sleep(2.0)

        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break

    return processed


if __name__ == "__main__":
    run_worker()
