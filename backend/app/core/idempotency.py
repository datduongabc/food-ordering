"""Idempotency-Key store for mutating endpoints (`POST /api/orders`, `POST /api/reservations`).

When a mobile or slow client times out while the server commits an order or booking, retrying
with the same `Idempotency-Key` header returns the original `201 Created` payload instead of
failing with `cart_empty` or creating duplicate reservations.
"""

import json
import logging
import threading
import time
from typing import Annotated, Any

from fastapi import Depends, Request
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_IDEMPOTENCY_TTL = 300


class IdempotencyStore:
    """In-memory idempotency store with TTL."""

    def __init__(self, *, ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[float, Any]] = {}

    def _compose_key(self, scope: str, key: str) -> str:
        return f"{scope}:{key.strip()}"

    def get(self, scope: str, key: str | None) -> Any | None:
        if not key or not key.strip():
            return None
        now = time.monotonic()
        ckey = self._compose_key(scope, key)
        with self._lock:
            entry = self._entries.get(ckey)
            if entry is None:
                return None
            expires_at, payload = entry
            if expires_at <= now:
                self._entries.pop(ckey, None)
                return None
            return payload

    def set(self, scope: str, key: str | None, payload: Any) -> None:
        if not key or not key.strip():
            return
        ckey = self._compose_key(scope, key)
        with self._lock:
            self._entries[ckey] = (time.monotonic() + self.ttl_seconds, payload)


class RedisIdempotencyStore(IdempotencyStore):
    """Shared Redis-backed idempotency store across uvicorn workers."""

    def __init__(
        self,
        client: Redis,
        *,
        prefix: str = "dateno",
        ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL,
    ) -> None:
        super().__init__(ttl_seconds=ttl_seconds)
        self._redis = client
        self._prefix = prefix
        self._fallback = IdempotencyStore(ttl_seconds=ttl_seconds)

    def _redis_key(self, scope: str, key: str) -> str:
        return f"{self._prefix}:idem:{scope}:{key.strip()}"

    def get(self, scope: str, key: str | None) -> Any | None:
        if not key or not key.strip():
            return None
        try:
            raw = self._redis.get(self._redis_key(scope, key))
            if raw is None:
                return None
            return json.loads(raw)
        except (RedisError, json.JSONDecodeError):
            logger.warning("Redis idempotency read failed; using fallback", exc_info=True)
            return self._fallback.get(scope, key)

    def set(self, scope: str, key: str | None, payload: Any) -> None:
        if not key or not key.strip():
            return
        self._fallback.set(scope, key, payload)
        try:
            self._redis.setex(
                self._redis_key(scope, key),
                self.ttl_seconds,
                json.dumps(payload),
            )
        except (RedisError, TypeError):
            logger.warning("Redis idempotency write failed", exc_info=True)


def build_idempotency_store(settings: Settings | None = None) -> IdempotencyStore:
    cfg = settings or get_settings()
    if not cfg.redis_configured:
        return IdempotencyStore()
    client = Redis.from_url(
        cfg.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return RedisIdempotencyStore(client, prefix=cfg.redis_key_prefix)


def get_idempotency_store(request: Request) -> IdempotencyStore:
    store: IdempotencyStore | None = getattr(request.app.state, "idempotency_store", None)
    if store is None:
        store = IdempotencyStore()
        request.app.state.idempotency_store = store
    return store


IdempotencyDep = Annotated[IdempotencyStore, Depends(get_idempotency_store)]
