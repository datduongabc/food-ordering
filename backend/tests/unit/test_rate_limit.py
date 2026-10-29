from app.core.rate_limit import Limit, RateLimiter

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
