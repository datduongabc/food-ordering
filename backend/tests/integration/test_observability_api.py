import json
import logging
import sys

import pytest

from app.core import observability
from app.core.config import Settings, get_settings
from app.core.observability import JsonFormatter, init_sentry


@pytest.fixture
def request_logs(caplog):
    with caplog.at_level(logging.INFO, logger="app.requests"):
        yield caplog


class TestRequestIds:
    def test_every_response_carries_a_fresh_id(self, client):
        first = client.get("/api/categories").headers["X-Request-ID"]
        second = client.get("/api/categories").headers["X-Request-ID"]
        assert len(first) == 32 and first != second

    def test_keeps_the_id_nginx_assigned(self, client):
        response = client.get("/api/categories", headers={"X-Request-ID": "abc123"})
        assert response.headers["X-Request-ID"] == "abc123"

    @pytest.mark.parametrize("forged", ["x\nINFO fake line", "a" * 65])
    def test_replaces_ids_that_could_forge_log_lines(self, client, forged):
        response = client.get("/api/categories", headers={"X-Request-ID": forged})
        assert response.headers["X-Request-ID"] != forged


class TestRequestLog:
    def test_logs_each_request_with_its_outcome(self, client, request_logs):
        response = client.get("/api/auth/me")

        [record] = [r for r in request_logs.records if r.name == "app.requests"]
        assert (record.method, record.path, record.status) == ("GET", "/api/auth/me", 401)
        assert record.request_id == response.headers["X-Request-ID"]
        assert record.duration_ms >= 0

    def test_skips_health_checks(self, client, request_logs):
        client.get("/api/health")
        assert not [r for r in request_logs.records if r.name == "app.requests"]

    def test_json_lines_hold_the_request_fields(self, client, request_logs):
        client.get("/api/auth/me", headers={"X-Request-ID": "req42"})
        [record] = [r for r in request_logs.records if r.name == "app.requests"]

        line = json.loads(JsonFormatter().format(record))

        assert line["message"] == "GET /api/auth/me 401"
        assert line["request_id"] == "req42"
        assert line["status"] == 401
        assert line["level"] == "INFO"

    def test_json_lines_include_exceptions(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            record = logging.LogRecord("app", logging.ERROR, "", 0, "failed", None, None)
            record.exc_info = sys.exc_info()
        line = json.loads(JsonFormatter().format(record))
        assert "RuntimeError: boom" in line["exception"]


class TestSentry:
    def test_off_without_a_dsn(self, monkeypatch):
        calls = []
        monkeypatch.setattr(observability.sentry_sdk, "init", lambda **kw: calls.append(kw))
        init_sentry(get_settings())
        assert calls == []

    def test_never_sends_personal_data(self, monkeypatch):
        calls = []
        monkeypatch.setattr(observability.sentry_sdk, "init", lambda **kw: calls.append(kw))
        init_sentry(Settings(sentry_dsn="https://key@o1.ingest.sentry.io/1", app_env="test"))

        [options] = calls
        assert options["environment"] == "test"
        assert options["send_default_pii"] is False
        assert options["max_request_body_size"] == "never"
