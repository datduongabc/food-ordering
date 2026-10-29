"""Stand-in reset codes for addresses with no account.

A real reset code turns wrong guesses into "too many attempts" after a few tries, while an
unknown address would answer "invalid code" forever, which tells an attacker the account
does not exist. These codes are issued and counted the same way, so both look identical.
Like the rate limiter they live in this process's memory.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from app.core.config import get_settings


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
