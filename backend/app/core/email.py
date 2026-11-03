import json
import logging
import smtplib
import time
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Annotated, Protocol

from fastapi import BackgroundTasks, Depends
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str


class EmailSender(Protocol):
    def send(self, email: Email) -> None: ...


class SmtpEmailSender:
    """Authenticated SMTP sender supporting STARTTLS (587) and implicit SSL/TLS (465)."""

    def __init__(self, settings: Settings):
        self._settings = settings

    def send(self, email: Email) -> None:
        message = EmailMessage()
        message["From"] = self._settings.mail_from or self._settings.smtp_username
        message["To"] = email.to
        message["Subject"] = email.subject
        message.set_content(email.text)

        smtp_cls = smtplib.SMTP_SSL if self._settings.smtp_use_ssl else smtplib.SMTP
        with smtp_cls(
            self._settings.smtp_host,
            self._settings.smtp_port,
            timeout=self._settings.smtp_timeout_seconds,
        ) as smtp:
            if self._settings.smtp_use_tls and not self._settings.smtp_use_ssl:
                smtp.starttls()
            smtp.login(self._settings.smtp_username, self._settings.smtp_password)
            smtp.send_message(message)


class ConsoleEmailSender:
    """Local development fallback: codes appear in the server log instead of on screen."""

    def send(self, email: Email) -> None:
        logger.warning("Email to %s | %s\n%s", email.to, email.subject, email.text)


class RedisEmailQueue:
    """Buffers outbound emails in Redis and drains them with retries so bursts at 2,000 CCU
    never lose mail to transient SMTP errors."""

    def __init__(
        self,
        redis_client: Redis,
        sender: EmailSender,
        *,
        prefix: str = "dateno",
        max_retries: int = 3,
        sleep: callable = time.sleep,
    ):
        self._redis = redis_client
        self._sender = sender
        self._queue_key = f"{prefix}:email:queue"
        self._dead_key = f"{prefix}:email:dead"
        self._max_retries = max(1, max_retries)
        self._sleep = sleep

    def enqueue(self, email: Email) -> None:
        payload = json.dumps(
            {"to": email.to, "subject": email.subject, "text": email.text, "attempts": 0}
        )
        self._redis.rpush(self._queue_key, payload)

    def drain_one(self) -> bool:
        raw = self._redis.lpop(self._queue_key)
        if raw is None:
            return False
        item = json.loads(raw)
        email = Email(to=item["to"], subject=item["subject"], text=item["text"])
        attempts = int(item.get("attempts", 0))
        while True:
            attempts += 1
            try:
                self._sender.send(email)
                return True
            except Exception:
                if attempts >= self._max_retries:
                    logger.exception(
                        "Failed to send email to %s after %d attempt(s)", email.to, attempts
                    )
                    item["attempts"] = attempts
                    self._redis.rpush(self._dead_key, json.dumps(item))
                    return False
                self._sleep(min(2.0, 0.2 * (2 ** (attempts - 1))))

    def send(self, email: Email) -> None:
        try:
            self.enqueue(email)
            self.drain_one()
        except RedisError:
            logger.warning("Redis email queue unavailable; sending directly", exc_info=True)
            self._sender.send(email)


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.smtp_configured:
        sender: EmailSender = SmtpEmailSender(settings)
        if settings.redis_configured:
            client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            return RedisEmailQueue(
                client,
                sender,
                prefix=settings.redis_key_prefix,
                max_retries=settings.smtp_max_retries,
            )
        return sender
    if settings.is_local:
        return ConsoleEmailSender()
    raise RuntimeError("SMTP is not configured; set SMTP_USERNAME and SMTP_PASSWORD.")


def send_safely(sender: EmailSender, email: Email) -> None:
    # Runs as a background task after the response is sent, so failures can only be logged.
    try:
        sender.send(email)
    except Exception:
        logger.exception("Failed to send email to %s", email.to)


Mailer = Annotated[EmailSender, Depends(get_email_sender)]


def notify(background: BackgroundTasks, mailer: EmailSender, email: Email | None) -> None:
    """Sends after the response, so a slow or failing mail server never holds up the request."""
    if email is not None:
        background.add_task(send_safely, mailer, email)
