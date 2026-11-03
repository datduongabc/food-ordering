import logging

import pytest
from redis.exceptions import RedisError

from app.core import email as email_module
from app.core.config import Settings
from app.core.email import (
    ConsoleEmailSender,
    Email,
    RedisEmailQueue,
    SmtpEmailSender,
    get_email_sender,
    send_safely,
)

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
    return Settings(_env_file=None, secret_key="s" * 32, **overrides)


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


class FakeQueueRedis:
    def __init__(self, *, broken: bool = False) -> None:
        self.broken = broken
        self.lists: dict[str, list[str]] = {}

    def rpush(self, key: str, value: str) -> None:
        if self.broken:
            raise RedisError("redis down")
        self.lists.setdefault(key, []).append(value)

    def lpop(self, key: str) -> str | None:
        if self.broken:
            raise RedisError("redis down")
        items = self.lists.get(key, [])
        return items.pop(0) if items else None


def test_smtp_sender_supports_implicit_ssl(monkeypatch):
    FakeSmtp.instances = []
    monkeypatch.setattr(email_module.smtplib, "SMTP_SSL", FakeSmtp)
    sender = SmtpEmailSender(
        settings(
            smtp_port=465,
            smtp_username="dateno@gmail.com",
            smtp_password="app-password",
            smtp_use_ssl=True,
        )
    )

    sender.send(CODE_EMAIL)

    (connection,) = FakeSmtp.instances
    assert connection.address == ("smtp.gmail.com", 465, 10)
    assert [call[0] for call in connection.calls] == ["login", "send"]


def test_redis_email_queue_retries_transient_errors_and_records_dead_letters():
    fake_redis = FakeQueueRedis()
    sent: list[Email] = []
    calls = 0

    class FlakySender:
        def send(self, email: Email) -> None:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise OSError("temporary SMTP hiccup")
            sent.append(email)

    queue = RedisEmailQueue(
        fake_redis,  # type: ignore[arg-type]
        FlakySender(),
        max_retries=3,
        sleep=lambda _: None,
    )
    queue.send(CODE_EMAIL)
    assert sent == [CODE_EMAIL]
    assert fake_redis.lists.get("dateno:email:dead") is None

    class AlwaysDown:
        def send(self, email: Email) -> None:
            raise OSError("SMTP down")

    dead_queue = RedisEmailQueue(
        fake_redis,  # type: ignore[arg-type]
        AlwaysDown(),
        max_retries=2,
        sleep=lambda _: None,
    )
    dead_queue.send(CODE_EMAIL)
    assert len(fake_redis.lists["dateno:email:dead"]) == 1


def test_redis_email_queue_falls_back_to_direct_send_when_redis_is_down(monkeypatch):
    sent: list[Email] = []

    class DirectSender:
        def send(self, email: Email) -> None:
            sent.append(email)

    queue = RedisEmailQueue(FakeQueueRedis(broken=True), DirectSender())  # type: ignore[arg-type]
    queue.send(CODE_EMAIL)
    assert sent == [CODE_EMAIL]

    monkeypatch.setattr(
        email_module,
        "get_settings",
        lambda: settings(
            smtp_username="a@gmail.com",
            smtp_password="x",
            redis_url="redis://localhost:6379/0",
        ),
    )
    assert isinstance(get_email_sender(), RedisEmailQueue)
