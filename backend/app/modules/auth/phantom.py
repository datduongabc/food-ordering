"""Stand-in reset codes for addresses with no account.

A real reset code turns wrong guesses into "too many attempts" after a few tries, while an
unknown address would answer "invalid code" forever, which tells an attacker the account
does not exist. These codes are issued and counted the same way, so both look identical.
When `REDIS_URL` is configured they live in Redis so multiple workers count together;
otherwise they fall back to in-process memory.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class _PhantomCode:
    expires_at: float
    attempts: int = 0


class PhantomResetCodes:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._codes: dict[str, _PhantomCode] = {}
        self._lock = threading.Lock()

    def issue(self, email: str) -> None:
        now = self._clock()
        ttl = get_settings().otp_ttl_minutes * 60
        with self._lock:
            # Issuing is rate-limited per address, so sweeping here keeps memory bounded.
            for stale in [key for key, code in self._codes.items() if code.expires_at <= now]:
                del self._codes[stale]
            self._codes[email] = _PhantomCode(expires_at=now + ttl)

    def record_guess(self, email: str) -> bool:
        """Counts a (necessarily wrong) guess. False means the code already took its maximum
        and `consume_otp` would answer "too many attempts"; True means "invalid code"."""
        with self._lock:
            code = self._codes.get(email)
            if code is None or code.expires_at <= self._clock():
                return True
            if code.attempts >= get_settings().otp_max_attempts:
                return False
            code.attempts += 1
            return True

    def __len__(self) -> int:
        return len(self._codes)


_PHANTOM_GUESS_LUA = """
local key = KEYS[1]
local max_attempts = tonumber(ARGV[1])
local current = redis.call('GET', key)
if not current then
    return 1
end
if tonumber(current) >= max_attempts then
    return 0
end
redis.call('INCR', key)
return 1
"""


class RedisPhantomResetCodes:
    """Shared stand-in reset codes backed by Redis with TTL and an atomic guess counter."""

    def __init__(
        self,
        redis_client: Redis,
        *,
        prefix: str = "dateno",
        fallback: PhantomResetCodes | None = None,
    ):
        self._redis = redis_client
        self._prefix = prefix
        self._fallback = fallback or PhantomResetCodes()

    def _redis_key(self, email: str) -> str:
        return f"{self._prefix}:phantom:{email}"

    def issue(self, email: str) -> None:
        ttl = get_settings().otp_ttl_minutes * 60
        try:
            self._redis.set(self._redis_key(email), 0, ex=ttl)
        except RedisError:
            logger.warning(
                "Redis phantom store unavailable; using in-memory fallback", exc_info=True
            )
            self._fallback.issue(email)

    def record_guess(self, email: str) -> bool:
        max_attempts = get_settings().otp_max_attempts
        try:
            allowed = int(
                self._redis.eval(_PHANTOM_GUESS_LUA, 1, self._redis_key(email), max_attempts)
            )
            return allowed == 1
        except RedisError:
            logger.warning(
                "Redis phantom store unavailable; using in-memory fallback", exc_info=True
            )
            return self._fallback.record_guess(email)


def build_phantom_reset_codes(
    settings: Settings | None = None,
) -> PhantomResetCodes | RedisPhantomResetCodes:
    cfg = settings or get_settings()
    if not cfg.redis_configured:
        return PhantomResetCodes()
    client = Redis.from_url(
        cfg.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return RedisPhantomResetCodes(client, prefix=cfg.redis_key_prefix)
