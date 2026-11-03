"""Server-Sent Events (SSE) broker with Redis Pub/Sub fan-out for real-time order and
reservation status updates across uvicorn workers.
"""

import asyncio
import contextlib
import json
import logging
import threading
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends, Request
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def format_sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class EventBroker:
    """In-process pub/sub broker with optional Redis fan-out across workers."""

    def __init__(self, redis_client: Redis | None = None, *, prefix: str = "dateno") -> None:
        self._redis = redis_client
        self._prefix = prefix
        self._lock = threading.Lock()
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)
        self._latest: dict[str, dict[str, Any]] = {}
        self.published_count = 0

    def _redis_channel(self, channel: str) -> str:
        return f"{self._prefix}:events:{channel}"

    def _redis_latest_key(self, channel: str) -> str:
        return f"{self._prefix}:events:latest:{channel}"

    def publish(self, channel: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self.published_count += 1
            self._latest[channel] = payload
            queues = list(self._subscribers.get(channel, ()))
        for q in queues:
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(payload)

        if self._redis is not None:
            try:
                encoded = json.dumps(payload)
                self._redis.setex(self._redis_latest_key(channel), 3600, encoded)
                self._redis.publish(self._redis_channel(channel), encoded)
            except RedisError:
                logger.warning("Failed to publish SSE event to Redis channel %s", channel)

    def latest(self, channel: str) -> dict[str, Any] | None:
        if self._redis is not None:
            try:
                raw = self._redis.get(self._redis_latest_key(channel))
                if raw is not None:
                    return json.loads(raw)
            except (RedisError, json.JSONDecodeError):
                pass
        with self._lock:
            return self._latest.get(channel)

    async def stream(
        self,
        channel: str,
        initial: dict[str, Any],
        *,
        once: bool = False,
        timeout_seconds: float = 15.0,
    ) -> AsyncIterator[str]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=32)
        with self._lock:
            self._subscribers[channel].add(q)
        try:
            yield format_sse("snapshot", initial)
            if once:
                latest = self.latest(channel)
                if latest is not None and latest != initial:
                    yield format_sse("update", latest)
                return

            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=timeout_seconds)
                    yield format_sse("update", payload)
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            with self._lock:
                subs = self._subscribers.get(channel)
                if subs is not None:
                    subs.discard(q)
                    if not subs:
                        self._subscribers.pop(channel, None)


def build_event_broker(settings: Settings | None = None) -> EventBroker:
    cfg = settings or get_settings()
    if not cfg.redis_configured:
        return EventBroker()
    client = Redis.from_url(
        cfg.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return EventBroker(client, prefix=cfg.redis_key_prefix)


def get_event_broker(request: Request) -> EventBroker:
    broker: EventBroker | None = getattr(request.app.state, "event_broker", None)
    if broker is None:
        broker = EventBroker()
        request.app.state.event_broker = broker
    return broker


BrokerDep = Annotated[EventBroker, Depends(get_event_broker)]
