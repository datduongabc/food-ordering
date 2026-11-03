"""Per-client request limits.

Counters live in Redis when `REDIS_URL` is configured so several uvicorn workers or replicas
share one sliding window and brute-force state; otherwise they fall back to in-process memory
for local development and unit tests.
"""

import logging
import math
import secrets
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Request
from redis import Redis
from redis.exceptions import RedisError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import Settings, get_settings
from app.core.deps import get_optional_user
from app.core.errors import TooManyRequestsError, error_body
from app.modules.users.models import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Limit:
    name: str
    requests: int
    seconds: int


# Every /api request from one address; generous enough for normal browsing, tight enough to
# stop scripted floods before they reach the database.
API_READS = Limit("api-read", 300, 60)
API_WRITES = Limit("api-write", 60, 60)

# Endpoints that send email, create accounts or accept guesses get their own, tighter limits.
LOGIN = Limit("login", 10, 60)
# Failed sign-ins per address and email, counted whether or not the account exists so the
# block reveals nothing. Replaces a per-account lockout, which let anyone lock anyone out.
LOGIN_FAILURES = Limit("login-failure", 5, 900)
REGISTER = Limit("register", 5, 3600)
PASSWORD_RESET_REQUESTS = Limit("password-reset-request", 10, 3600)
PASSWORD_RESET_PER_EMAIL = Limit("password-reset-email", 3, 900)
CODE_ENTRY = Limit("code-entry", 10, 900)
VERIFICATION_EMAILS = Limit("verification-email", 3, 900)
REVIEWS = Limit("review", 10, 3600)
REVIEW_PHOTOS = Limit("review-photo", 15, 3600)
ORDERS = Limit("order", 10, 600)
PAYMENTS = Limit("payment", 20, 600)
BOOKINGS = Limit("booking", 5, 3600)
PROMO_CHECKS = Limit("promo-check", 20, 600)


class RateLimiter:
    """Sliding-window counters: a request is allowed when fewer than `requests` were allowed
    in the last `seconds`. Refused requests are not counted, so waiting always helps."""

    SWEEP_EVERY = 1000

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: dict[tuple[str, str], tuple[int, deque[float]]] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, limit: Limit, key: str) -> int | None:
        """Counts a request; returns the seconds to wait instead when over the limit."""
        now = self._clock()
        with self._lock:
            wait = self._wait(limit, key, now)
            if wait is not None:
                return wait
            self._hits[(limit.name, key)][1].append(now)
            self._calls += 1
            if self._calls % self.SWEEP_EVERY == 0:
                self._sweep(now)
            return None

    def wait(self, limit: Limit, key: str) -> int | None:
        """The seconds to wait if the limit is reached, without counting a request."""
        with self._lock:
            return self._wait(limit, key, self._clock())

    def forget(self, limit: Limit, key: str) -> None:
        with self._lock:
            self._hits.pop((limit.name, key), None)

    def _wait(self, limit: Limit, key: str, now: float) -> int | None:
        _, hits = self._hits.setdefault((limit.name, key), (limit.seconds, deque()))
        while hits and hits[0] <= now - limit.seconds:
            hits.popleft()
        if len(hits) >= limit.requests:
            return max(1, math.ceil(hits[0] + limit.seconds - now))
        return None

    def _sweep(self, now: float) -> None:
        # Forget clients whose every hit has left its window, so memory tracks active clients.
        stale = [
            key
            for key, (seconds, hits) in self._hits.items()
            if not hits or hits[-1] <= now - seconds
        ]
        for key in stale:
            del self._hits[key]

    def __len__(self) -> int:
        return len(self._hits)


_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local record_hit = tonumber(ARGV[4])
local member = ARGV[5]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now_ms - window_ms)
local count = redis.call('ZCARD', key)
if count >= max_requests then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local oldest_ms = tonumber(oldest[2])
    local wait_ms = (oldest_ms + window_ms) - now_ms
    local wait_s = math.ceil(wait_ms / 1000.0)
    if wait_s < 1 then
        wait_s = 1
    end
    return wait_s
end
if record_hit == 1 then
    redis.call('ZADD', key, now_ms, member)
    redis.call('PEXPIRE', key, window_ms)
end
return 0
"""


class RedisRateLimiter:
    """Shared sliding-window counters backed by Redis ZSETs and an atomic Lua script.

    Falls back to an in-memory `RateLimiter` if Redis is temporarily unreachable, so a brief
    broker blip does not take down the API.
    """

    def __init__(
        self,
        redis_client: Redis,
        *,
        prefix: str = "dateno",
        clock: Callable[[], float] = time.time,
        fallback: RateLimiter | None = None,
    ):
        self._redis = redis_client
        self._prefix = prefix
        self._clock = clock
        self._fallback = fallback or RateLimiter()

    def _redis_key(self, limit: Limit, key: str) -> str:
        return f"{self._prefix}:rl:{limit.name}:{key}"

    def _eval(self, limit: Limit, key: str, *, record_hit: bool) -> int | None:
        now_ms = int(self._clock() * 1000)
        window_ms = limit.seconds * 1000
        member = f"{now_ms}:{secrets.token_hex(4)}" if record_hit else ""
        wait = int(
            self._redis.eval(
                _SLIDING_WINDOW_LUA,
                1,
                self._redis_key(limit, key),
                now_ms,
                window_ms,
                limit.requests,
                1 if record_hit else 0,
                member,
            )
        )
        return wait if wait > 0 else None

    def hit(self, limit: Limit, key: str) -> int | None:
        try:
            return self._eval(limit, key, record_hit=True)
        except RedisError:
            logger.warning(
                "Redis rate limiter unavailable; using in-memory fallback", exc_info=True
            )
            return self._fallback.hit(limit, key)

    def wait(self, limit: Limit, key: str) -> int | None:
        try:
            return self._eval(limit, key, record_hit=False)
        except RedisError:
            logger.warning(
                "Redis rate limiter unavailable; using in-memory fallback", exc_info=True
            )
            return self._fallback.wait(limit, key)

    def forget(self, limit: Limit, key: str) -> None:
        self._fallback.forget(limit, key)
        try:
            self._redis.delete(self._redis_key(limit, key))
        except RedisError:
            logger.warning("Failed to clear Redis rate-limit key %s", key, exc_info=True)


def build_rate_limiter(settings: Settings | None = None) -> RateLimiter | RedisRateLimiter:
    cfg = settings or get_settings()
    if not cfg.redis_configured:
        return RateLimiter()
    client = Redis.from_url(
        cfg.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return RedisRateLimiter(client, prefix=cfg.redis_key_prefix)


def too_many_requests(seconds: int) -> TooManyRequestsError:
    return TooManyRequestsError(
        f"Too many requests. Please try again in {seconds} second(s).",
        code="rate_limited",
        params={"seconds": seconds},
        headers={"Retry-After": str(seconds)},
    )


def client_ip(request: Request) -> str:
    # uvicorn's proxy-headers support has already replaced this with the address nginx saw.
    return request.client.host if request.client else "unknown"


def enforce(request: Request, limit: Limit, key: str) -> None:
    if not get_settings().rate_limits_enabled:
        return
    wait = request.app.state.rate_limiter.hit(limit, key)
    if wait is not None:
        raise too_many_requests(wait)


def rate_limit(limit: Limit, per: Literal["ip", "user"] = "ip"):
    """A route dependency counting requests per client address, or per signed-in account
    (falling back to the address for guests)."""
    if per == "ip":

        def ip_dependency(request: Request) -> None:
            enforce(request, limit, f"ip:{client_ip(request)}")

        return Depends(ip_dependency)

    def user_dependency(
        request: Request, user: Annotated[User | None, Depends(get_optional_user)]
    ) -> None:
        key = f"user:{user.id}" if user else f"ip:{client_ip(request)}"
        enforce(request, limit, key)

    return Depends(user_dependency)


class RateLimitMiddleware:
    """Applies the API-wide read and write limits before any route runs."""

    EXEMPT = frozenset({"/api/health", "/api/health/ready", "/api/metrics"})

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or not path.startswith("/api/")
            or path in self.EXEMPT
            or not get_settings().rate_limits_enabled
        ):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        limit = API_READS if request.method in {"GET", "HEAD", "OPTIONS"} else API_WRITES
        wait = scope["app"].state.rate_limiter.hit(limit, client_ip(request))
        if wait is None:
            await self.app(scope, receive, send)
            return

        error = too_many_requests(wait)
        response = JSONResponse(
            error_body(error.detail, error.code, error.params),
            status_code=error.status_code,
            headers=error.headers,
        )
        await response(scope, receive, send)
