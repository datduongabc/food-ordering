import logging

import pytest

from app.core import email as email_module
from app.core.config import Settings
from app.core.email import ConsoleEmailSender, Email, SmtpEmailSender, get_email_sender, send_safely

CODE_EMAIL = Email(to="lan@example.com", subject="Mã xác thực", text="Mã của bạn: 123456")


class FakeSmtp:
    """Stands in for smtplib.SMTP and records what a sender did with it."""

    instances: list["FakeSmtp"] = []

    def __init__(self, host: str, port: int, timeout: int):
        self.address = (host, port, timeout)
        self.calls: list[tuple] = []
        FakeSmtp.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.calls.append(("starttls",))

    def login(self, username, password):
        self.calls.append(("login", username, password))

    def send_message(self, message):
        self.calls.append(("send", message))


@pytest.fixture
def smtp(monkeypatch) -> type[FakeSmtp]:
    FakeSmtp.instances = []
    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSmtp)
    return FakeSmtp


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_smtp_sender_logs_in_over_tls_and_sends_from_mail_from(smtp):
    sender = SmtpEmailSender(
        settings(
            smtp_username="dateno@gmail.com",
            smtp_password="app-password",
            mail_from="DaTeNO <dateno@gmail.com>",
        )
    )

    sender.send(CODE_EMAIL)

    (connection,) = smtp.instances
    assert connection.address == ("smtp.gmail.com", 587, 10)
    assert [call[0] for call in connection.calls] == ["starttls", "login", "send"]
    assert connection.calls[1] == ("login", "dateno@gmail.com", "app-password")
    message = connection.calls[2][1]
    assert message["From"] == "DaTeNO <dateno@gmail.com>"
    assert message["To"] == "lan@example.com"
    assert message["Subject"] == "Mã xác thực"
    assert "123456" in message.get_content()


def test_smtp_sender_falls_back_to_the_username_as_sender(smtp):
    SmtpEmailSender(settings(smtp_username="dateno@gmail.com", smtp_password="x")).send(CODE_EMAIL)

    assert smtp.instances[0].calls[2][1]["From"] == "dateno@gmail.com"


def test_console_sender_writes_the_email_to_the_log(caplog):
    with caplog.at_level(logging.WARNING, logger="app.core.email"):
        ConsoleEmailSender().send(CODE_EMAIL)

    assert "Email to lan@example.com | Mã xác thực" in caplog.text
    assert "123456" in caplog.text


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"smtp_username": "a@gmail.com", "smtp_password": "x"}, SmtpEmailSender),
        (
            {"smtp_username": "a@gmail.com", "smtp_password": "x", "app_env": "production"},
            SmtpEmailSender,
        ),
        ({}, ConsoleEmailSender),
    ],
)
def test_sender_is_smtp_when_configured_else_console_locally(monkeypatch, overrides, expected):
    monkeypatch.setattr(email_module, "get_settings", lambda: settings(**overrides))

    assert isinstance(get_email_sender(), expected)


def test_production_without_smtp_refuses_to_start_sending(monkeypatch):
    # Codes printed to a production log would let anyone with log access take over accounts.
    monkeypatch.setattr(email_module, "get_settings", lambda: settings(app_env="production"))

    with pytest.raises(RuntimeError, match="SMTP is not configured"):
        get_email_sender()


def test_send_safely_logs_a_failure_instead_of_raising(caplog):
    class Broken:
        def send(self, email):
            raise OSError("connection refused")

    with caplog.at_level(logging.ERROR, logger="app.core.email"):
        send_safely(Broken(), CODE_EMAIL)

    assert "Failed to send email to lan@example.com" in caplog.text
