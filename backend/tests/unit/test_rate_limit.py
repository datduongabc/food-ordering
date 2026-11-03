import math

from redis.exceptions import RedisError

from app.core.config import Settings
from app.core.rate_limit import Limit, RateLimiter, RedisRateLimiter, build_rate_limiter

LIMIT = Limit("test", requests=3, seconds=60)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_the_limit_then_says_how_long_to_wait():
    clock = Clock()
    limiter = RateLimiter(clock)

    assert [limiter.hit(LIMIT, "ip:1") for _ in range(3)] == [None, None, None]
    clock.now += 20
    assert limiter.hit(LIMIT, "ip:1") == 40


def test_the_window_slides_so_old_requests_stop_counting():
    clock = Clock()
    limiter = RateLimiter(clock)
    limiter.hit(LIMIT, "ip:1")
    clock.now += 30
    limiter.hit(LIMIT, "ip:1")
    limiter.hit(LIMIT, "ip:1")

    clock.now += 30  # the first request has just left the window
    assert limiter.hit(LIMIT, "ip:1") is None
    assert limiter.hit(LIMIT, "ip:1") == 30


def test_refused_requests_are_not_counted():
    clock = Clock()
    limiter = RateLimiter(clock)
    for _ in range(3):
        limiter.hit(LIMIT, "ip:1")
    for _ in range(50):
        limiter.hit(LIMIT, "ip:1")

    clock.now += 60
    assert limiter.hit(LIMIT, "ip:1") is None


def test_clients_and_limits_are_counted_separately():
    limiter = RateLimiter(Clock())
    for _ in range(3):
        limiter.hit(LIMIT, "ip:1")

    assert limiter.hit(LIMIT, "ip:2") is None
    assert limiter.hit(Limit("other", 3, 60), "ip:1") is None


def test_wait_is_never_reported_as_zero():
    clock = Clock()
    limiter = RateLimiter(clock)
    for _ in range(3):
        limiter.hit(LIMIT, "ip:1")
    clock.now += 59.9

    assert limiter.hit(LIMIT, "ip:1") == 1


def test_idle_clients_are_forgotten(monkeypatch):
    clock = Clock()
    limiter = RateLimiter(clock)
    monkeypatch.setattr(RateLimiter, "SWEEP_EVERY", 2)
    limiter.hit(LIMIT, "ip:idle")
    clock.now += 61

    limiter.hit(LIMIT, "ip:active")  # second call: sweeps

    assert len(limiter) == 1


def test_wait_peeks_without_counting_and_forget_starts_over():
    limiter = RateLimiter(Clock())
    assert limiter.wait(LIMIT, "ip:1") is None
    for _ in range(3):
        limiter.hit(LIMIT, "ip:1")

    assert limiter.wait(LIMIT, "ip:1") == 60
    limiter.forget(LIMIT, "ip:1")
    assert limiter.wait(LIMIT, "ip:1") is None


class FakeRedisZSet:
    """In-memory double executing the sliding-window ZSET Lua script semantics."""

    def __init__(self, *, broken: bool = False) -> None:
        self.broken = broken
        self.zsets: dict[str, list[tuple[int, str]]] = {}
        self.ttls: dict[str, int] = {}

    def eval(
        self,
        _script: str,
        _numkeys: int,
        key: str,
        now_ms: int,
        window_ms: int,
        max_requests: int,
        record_hit: int,
        member: str,
    ) -> int:
        if self.broken:
            raise RedisError("connection lost")
        entries = [(score, m) for score, m in self.zsets.get(key, []) if score > now_ms - window_ms]
        self.zsets[key] = entries
        if len(entries) >= max_requests:
            oldest_ms = entries[0][0]
            return max(1, math.ceil((oldest_ms + window_ms - now_ms) / 1000.0))
        if record_hit == 1:
            entries.append((now_ms, member))
            self.ttls[key] = window_ms
        return 0

    def delete(self, key: str) -> None:
        if self.broken:
            raise RedisError("connection lost")
        self.zsets.pop(key, None)
        self.ttls.pop(key, None)


def test_redis_rate_limiter_sliding_window_wait_and_forget():
    clock = Clock()
    fake_redis = FakeRedisZSet()
    limiter = RedisRateLimiter(fake_redis, clock=clock)  # type: ignore[arg-type]

    assert [limiter.hit(LIMIT, "ip:1") for _ in range(3)] == [None, None, None]
    clock.now += 20
    assert limiter.wait(LIMIT, "ip:1") == 40
    assert limiter.hit(LIMIT, "ip:1") == 40

    clock.now += 40
    assert limiter.hit(LIMIT, "ip:1") is None

    limiter.forget(LIMIT, "ip:1")
    assert limiter.wait(LIMIT, "ip:1") is None


def test_redis_rate_limiter_falls_back_to_memory_when_redis_fails():
    clock = Clock()
    limiter = RedisRateLimiter(FakeRedisZSet(broken=True), clock=clock)  # type: ignore[arg-type]

    assert [limiter.hit(LIMIT, "ip:1") for _ in range(3)] == [None, None, None]
    assert limiter.wait(LIMIT, "ip:1") is not None
    assert limiter.hit(LIMIT, "ip:1") is not None
    limiter.forget(LIMIT, "ip:1")
    assert limiter.wait(LIMIT, "ip:1") is None


def test_build_rate_limiter_selects_memory_or_redis():
    assert isinstance(build_rate_limiter(Settings(_env_file=None, redis_url="")), RateLimiter)
    assert isinstance(
        build_rate_limiter(Settings(_env_file=None, redis_url="redis://localhost:6379/0")),
        RedisRateLimiter,
    )
