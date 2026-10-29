import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

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
    def __init__(self, settings: Settings):
        self._settings = settings

    def send(self, email: Email) -> None:
        message = EmailMessage()
        message["From"] = self._settings.mail_from or self._settings.smtp_username
        message["To"] = email.to
        message["Subject"] = email.subject
        message.set_content(email.text)

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(self._settings.smtp_username, self._settings.smtp_password)
            smtp.send_message(message)


class ConsoleEmailSender:
    """Local development fallback: codes appear in the server log instead of on screen."""

    def send(self, email: Email) -> None:
        logger.warning("Email to %s | %s\n%s", email.to, email.subject, email.text)


def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.smtp_configured:
        return SmtpEmailSender(settings)
    if settings.is_local:
        return ConsoleEmailSender()
    raise RuntimeError("SMTP is not configured; set SMTP_USERNAME and SMTP_PASSWORD.")


def send_safely(sender: EmailSender, email: Email) -> None:
    # Runs as a background task after the response is sent, so failures can only be logged.
    try:
        sender.send(email)
    except Exception:
        logger.exception("Failed to send email to %s", email.to)
