from datetime import time
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


DEFAULT_SECRET_KEY = "change-me-in-production"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    secret_key: str = DEFAULT_SECRET_KEY

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/food_ordering_db"

    # Uploaded and seeded images; served at /media. Mount a volume here in production.
    media_dir: Path = BACKEND_DIR / "media"
    media_url: str = "/media"

    # Cookies are only marked Secure outside local development, where the dev server is plain HTTP.
    session_cookie_name: str = "dateno_session"
    csrf_cookie_name: str = "dateno_csrf"
    session_ttl_hours: int = 12
    remember_me_ttl_days: int = 7

    otp_ttl_minutes: int = 15
    otp_max_attempts: int = 5
    login_max_failures: int = 5
    login_lockout_minutes: int = 15

    # Booking rules are evaluated in the restaurant's local time, not the server's.
    restaurant_timezone: str = "Asia/Ho_Chi_Minh"
    reservation_max_days_ahead: int = 3
    reservation_max_guests: int = 10
    # First and last time a table can be booked for; the kitchen closes an hour after.
    reservation_opening_time: time = time(10, 0)
    reservation_last_seating_time: time = time(21, 0)

    # Off only for end-to-end suites, which sign up many accounts from one address in seconds.
    rate_limits_enabled: bool = True

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    mail_from: str = ""

    @model_validator(mode="after")
    def _production_needs_a_real_secret(self) -> "Settings":
        # The key signs one-time codes; a guessable one would let anyone forge them.
        if self.app_env == "production" and (
            self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < MIN_SECRET_KEY_LENGTH
        ):
            raise ValueError(
                f"SECRET_KEY must be set to a random value of at least {MIN_SECRET_KEY_LENGTH} "
                "characters in production."
            )
        return self

    @property
    def is_local(self) -> bool:
        return self.app_env in ("local", "test")

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
