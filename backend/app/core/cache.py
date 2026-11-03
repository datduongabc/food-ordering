"""Read-through Redis cache with O(1) versioned invalidation for catalog and session data.

When `REDIS_URL` is configured, uvicorn workers share cached JSON payloads in Redis under a
versioned key namespace (`{prefix}:cache:catalog:v{ver}:{key}`). Calling `invalidate()`
atomically increments the version counter (`INCR`), expiring old keys via TTL without
expensive `SCAN`/`DEL` loops.
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

DEFAULT_TTL_SECONDS = 300


class CatalogCache:
    """In-memory versioned cache with TTL, used directly in unit tests or as a fallback."""

    def __init__(self, *, enabled: bool = True, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._version = 1
        self._store: dict[str, tuple[float, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.invalidations = 0

    def _versioned_key(self, key: str) -> str:
        return f"v{self._version}:{key}"

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        now = time.monotonic()
        with self._lock:
            vkey = self._versioned_key(key)
            entry = self._store.get(vkey)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at <= now:
                self._store.pop(vkey, None)
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._store[self._versioned_key(key)] = (expires_at, value)

    def invalidate(self) -> int:
        with self._lock:
            self._version += 1
            self._store.clear()
            self.invalidations += 1
            return self._version


class RedisCatalogCache(CatalogCache):
    """Shared Redis-backed catalog cache across multi-worker uvicorn processes."""

    def __init__(
        self,
        client: Redis,
        *,
        prefix: str = "dateno",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        super().__init__(enabled=True, ttl_seconds=ttl_seconds)
        self._redis = client
        self._prefix = prefix
        self._ver_key = f"{prefix}:cache:catalog:ver"
        self._hits_key = f"{prefix}:cache:catalog:hits"
        self._misses_key = f"{prefix}:cache:catalog:misses"

    def _current_version(self) -> str:
        ver = self._redis.get(self._ver_key)
        return str(ver) if ver is not None else "0"

    def _redis_key(self, key: str) -> str:
        ver = self._current_version()
        return f"{self._prefix}:cache:catalog:v{ver}:{key}"

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            return None
        try:
            raw = self._redis.get(self._redis_key(key))
            if raw is None:
                self.misses += 1
                self._redis.incr(self._misses_key)
                return None
            self.hits += 1
            self._redis.incr(self._hits_key)
            return json.loads(raw)
        except (RedisError, json.JSONDecodeError):
            logger.warning("Redis catalog cache read failed; bypassing cache", exc_info=True)
            return None

    def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        try:
            payload = json.dumps(value)
            self._redis.setex(self._redis_key(key), ttl, payload)
        except (RedisError, TypeError):
            logger.warning("Redis catalog cache write failed; skipping", exc_info=True)

    def invalidate(self) -> int:
        with self._lock:
            self.invalidations += 1
        try:
            return int(self._redis.incr(self._ver_key))
        except RedisError:
            logger.warning("Redis catalog cache invalidation failed", exc_info=True)
            return super().invalidate()

    def stats(self) -> dict[str, int]:
        try:
            hits = int(self._redis.get(self._hits_key) or 0)
            misses = int(self._redis.get(self._misses_key) or 0)
            ver = int(self._redis.get(self._ver_key) or 0)
            return {"hits": hits, "misses": misses, "version": ver}
        except RedisError:
            return {"hits": self.hits, "misses": self.misses, "version": self._version}


def build_catalog_cache(settings: Settings | None = None) -> CatalogCache:
    cfg = settings or get_settings()
    if not cfg.redis_configured:
        # Disabled by default when Redis is absent so integration tests that mutate SQLite
        # rows directly via fixtures never observe stale in-process state.
        return CatalogCache(enabled=False)
    client = Redis.from_url(
        cfg.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return RedisCatalogCache(client, prefix=cfg.redis_key_prefix)


def get_catalog_cache(request: Request) -> CatalogCache:
    cache: CatalogCache | None = getattr(request.app.state, "catalog_cache", None)
    if cache is None:
        cache = CatalogCache(enabled=False)
    return cache


def invalidate_catalog_cache(request: Request) -> None:
    get_catalog_cache(request).invalidate()


CacheDep = Annotated[CatalogCache, Depends(get_catalog_cache)]
