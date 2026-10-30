"""Per-client request limits.

Counters live in this process's memory, which suits the single uvicorn worker the app runs
as. Several workers or replicas would each count on their own; move the store to Redis
before scaling out.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings
from app.core.deps import get_optional_user
from app.core.errors import TooManyRequestsError, error_body
from app.modules.users.models import User


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

    def dependency(
        request: Request, user: Annotated[User | None, Depends(get_optional_user)]
    ) -> None:
        key = f"user:{user.id}" if per == "user" and user else f"ip:{client_ip(request)}"
        enforce(request, limit, key)

    return Depends(dependency)


class RateLimitMiddleware:
    """Applies the API-wide read and write limits before any route runs."""

    EXEMPT = frozenset({"/api/health"})

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
