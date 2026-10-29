from app.core.config import get_settings
from app.modules.auth.phantom import PhantomResetCodes
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
