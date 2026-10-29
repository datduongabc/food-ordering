from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    secret_key: str = "change-me-in-production"

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

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    mail_from: str = ""

    @property
    def is_local(self) -> bool:
        return self.app_env in ("local", "test")

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
