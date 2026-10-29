import bcrypt

from app.core.security import (
    hash_otp_code,
    hash_password,
    hash_token,
    new_otp_code,
    new_session_token,
    verify_password,
)


def test_password_hash_roundtrip_uses_argon2():
    hashed = hash_password("correct-horse")

    assert hashed.startswith("$argon2")
    assert verify_password("correct-horse", hashed) == (True, None)
    assert verify_password("wrong-horse", hashed)[0] is False


def test_legacy_php_bcrypt_hash_verifies_and_requests_upgrade():
    # PHP's password_hash() emits the $2y$ prefix, which must keep working after the migration.
    legacy = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode().replace("$2b$", "$2y$", 1)

    valid, upgraded = verify_password("correct-horse", legacy)

    assert valid is True
    assert upgraded is not None and upgraded.startswith("$argon2")


def test_otp_codes_are_six_digits():
    codes = {new_otp_code() for _ in range(200)}

    assert all(len(code) == 6 and code.isdigit() for code in codes)
    assert len(codes) > 150  # random, not a constant


def test_otp_hash_is_keyed_and_deterministic():
    assert hash_otp_code("123456") == hash_otp_code("123456")
    assert hash_otp_code("123456") != hash_otp_code("123457")
    assert hash_otp_code("123456") != hash_token("123456")


def test_session_tokens_are_unique_and_hash_to_fixed_length():
    first, second = new_session_token(), new_session_token()

    assert first != second
    assert len(hash_token(first)) == 64
