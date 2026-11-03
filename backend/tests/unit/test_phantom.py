from redis.exceptions import RedisError

from app.core.config import Settings, get_settings
from app.modules.auth.phantom import (
    PhantomResetCodes,
    RedisPhantomResetCodes,
    build_phantom_reset_codes,
)
from tests.unit.test_rate_limit import Clock


def test_counts_guesses_like_a_real_code_until_it_expires():
    clock = Clock()
    codes = PhantomResetCodes(clock)
    max_attempts = get_settings().otp_max_attempts
    codes.issue("a@example.com")

    assert [codes.record_guess("a@example.com") for _ in range(max_attempts)] == [
        True
    ] * max_attempts
    assert codes.record_guess("a@example.com") is False
    # Expired, a real code answers "invalid" again until a new one is requested.
    clock.now += get_settings().otp_ttl_minutes * 60
    assert codes.record_guess("a@example.com") is True


def test_addresses_without_a_request_are_never_blocked():
    codes = PhantomResetCodes(Clock())
    assert all(codes.record_guess("a@example.com") for _ in range(10))


def test_expired_codes_are_swept_when_new_ones_are_issued():
    clock = Clock()
    codes = PhantomResetCodes(clock)
    codes.issue("a@example.com")
    clock.now += get_settings().otp_ttl_minutes * 60
    codes.issue("b@example.com")
    assert len(codes) == 1


class FakePhantomRedis:
    def __init__(self, *, broken: bool = False) -> None:
        self.broken = broken
        self.store: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    def set(self, key: str, value: int, ex: int) -> None:
        if self.broken:
            raise RedisError("redis down")
        self.store[key] = int(value)
        self.ttls[key] = ex

    def eval(self, _script: str, _numkeys: int, key: str, max_attempts: int) -> int:
        if self.broken:
            raise RedisError("redis down")
        if key not in self.store:
            return 1
        if self.store[key] >= max_attempts:
            return 0
        self.store[key] += 1
        return 1


def test_redis_phantom_codes_count_guesses_and_fall_back_on_error():
    fake = FakePhantomRedis()
    codes = RedisPhantomResetCodes(fake)  # type: ignore[arg-type]
    max_attempts = get_settings().otp_max_attempts

    assert codes.record_guess("nobody@example.com") is True
    codes.issue("a@example.com")
    assert [codes.record_guess("a@example.com") for _ in range(max_attempts)] == [
        True
    ] * max_attempts
    assert codes.record_guess("a@example.com") is False

    broken = RedisPhantomResetCodes(FakePhantomRedis(broken=True))  # type: ignore[arg-type]
    broken.issue("b@example.com")
    assert [broken.record_guess("b@example.com") for _ in range(max_attempts)] == [
        True
    ] * max_attempts
    assert broken.record_guess("b@example.com") is False


def test_build_phantom_reset_codes_selects_memory_or_redis():
    assert isinstance(
        build_phantom_reset_codes(Settings(_env_file=None, redis_url="")), PhantomResetCodes
    )
    assert isinstance(
        build_phantom_reset_codes(Settings(_env_file=None, redis_url="redis://localhost:6379/0")),
        RedisPhantomResetCodes,
    )
