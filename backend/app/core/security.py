import base64
import hashlib
import hmac
import json
import secrets

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import get_settings

# Argon2 for new hashes; bcrypt stays verifiable so accounts imported from the PHP app keep working.
_password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Returns (valid, upgraded_hash); upgraded_hash is set when the stored hash is outdated."""
    return _password_hash.verify_and_update(password, password_hash)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    # Session tokens carry 256 bits of entropy, so a plain digest is enough to protect them at rest.
    return hashlib.sha256(token.encode()).hexdigest()


def new_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp_code(code: str) -> str:
    # A bare digest of a 6-digit code is trivially brute-forced, so it is keyed with the secret.
    key = get_settings().secret_key.encode()
    return hmac.new(key, code.encode(), hashlib.sha256).hexdigest()


def create_email_verification_token(user_id: int, email: str, code: str) -> str:
    """Signs (user_id, email, code) with SECRET_KEY so a link in the inbox can verify the
    account in one click, even when opened in another browser or on a phone."""
    raw = json.dumps([user_id, email, code], separators=(",", ":")).encode()
    payload = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    key = get_settings().secret_key.encode()
    sig = hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_email_verification_token(token: str) -> tuple[int, str, str] | None:
    """Returns (user_id, email, code) when the signature is valid, or None."""
    payload, dot, sig = token.strip().partition(".")
    if not dot or not payload or not sig:
        return None
    key = get_settings().secret_key.encode()
    expected = hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        padded = payload + "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except Exception:
        return None
    if (
        isinstance(data, list)
        and len(data) == 3
        and isinstance(data[0], int)
        and isinstance(data[1], str)
        and isinstance(data[2], str)
    ):
        return data[0], data[1], data[2]
    return None
