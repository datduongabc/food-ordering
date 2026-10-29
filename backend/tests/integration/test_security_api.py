import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.rate_limit import API_WRITES, LOGIN, PASSWORD_RESET_PER_EMAIL, REGISTER
from app.main import create_app
from tests.data import USER


def login(client: TestClient, email: str = "nobody@example.com"):
    return client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})


def assert_rate_limited(response, window: int) -> None:
    assert response.status_code == 429
    body = response.json()
    assert body["code"] == "rate_limited"
    assert 0 < body["params"]["seconds"] <= window
    assert response.headers["Retry-After"] == str(body["params"]["seconds"])


class TestRouteLimits:
    def test_login_attempts_are_limited_per_address(self, client):
        for _ in range(LOGIN.requests):
            assert login(client).status_code == 401

        assert_rate_limited(login(client), LOGIN.seconds)
        # The limit is on the caller, not the account they try.
        assert_rate_limited(login(client, "someone-else@example.com"), LOGIN.seconds)

    def test_sign_ups_are_limited_per_address(self, client):
        for n in range(REGISTER.requests):
            account = {**USER, "email": f"user{n}@example.com", "phone": f"090000000{n}"}
            assert client.post("/api/auth/register", json=account).status_code == 201

        response = client.post(
            "/api/auth/register", json={**USER, "email": "late@example.com", "phone": "0911111111"}
        )
        assert_rate_limited(response, REGISTER.seconds)

    def test_reset_emails_are_limited_per_address_whatever_its_case(self, client, registered_user):
        def forgot(email):
            return client.post("/api/auth/password/forgot", json={"email": email})

        for _ in range(PASSWORD_RESET_PER_EMAIL.requests):
            assert forgot(USER["email"]).status_code == 202

        assert_rate_limited(forgot(USER["email"].upper()), PASSWORD_RESET_PER_EMAIL.seconds)
        # Unknown addresses are counted the same, and other inboxes are unaffected.
        assert forgot("other@example.com").status_code == 202

    def test_verification_emails_are_limited_per_account(self, logged_in_client, outbox):
        for _ in range(3):
            assert logged_in_client.post("/api/auth/email/verification").status_code == 202

        response = logged_in_client.post("/api/auth/email/verification")
        assert_rate_limited(response, 900)
        assert len(outbox.sent) == 3

    def test_limits_can_be_switched_off(self, client, monkeypatch):
        monkeypatch.setattr(get_settings(), "rate_limits_enabled", False)
        for _ in range(LOGIN.requests + 1):
            assert login(client).status_code == 401


class TestApiWideLimit:
    def test_writes_are_limited_across_endpoints(self, client):
        for _ in range(API_WRITES.requests):
            assert client.post("/api/auth/logout").status_code == 204

        assert_rate_limited(client.post("/api/cart/items", json={}), API_WRITES.seconds)
        # Reads have their own allowance, and the health check is never limited.
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/health").status_code == 200

    def test_each_app_counts_on_its_own(self, client):
        for _ in range(API_WRITES.requests):
            client.post("/api/auth/logout")

        with TestClient(create_app()) as fresh:
            fresh.get("/api/health")
            fresh.headers["X-CSRF-Token"] = fresh.cookies[get_settings().csrf_cookie_name]
            assert fresh.post("/api/auth/logout").status_code == 204


class TestHeaders:
    def test_api_responses_are_hardened_and_never_cached(self, client):
        response = client.get("/api/health")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Cache-Control"] == "no-store"

    def test_errors_carry_the_headers_too(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_media_is_hardened_but_cacheable(self, client, media_dir):
        (media_dir / "products" / "pho.jpg").write_bytes(b"\xff\xd8\xff")

        response = client.get("/media/products/pho.jpg")

        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "no-store" not in response.headers.get("Cache-Control", "")


class TestProduction:
    def test_api_docs_are_hidden(self, monkeypatch):
        monkeypatch.setattr(get_settings(), "app_env", "production")
        with TestClient(create_app()) as client:
            assert client.get("/api/docs").status_code == 404
            assert client.get("/api/openapi.json").status_code == 404

    def test_api_docs_are_served_locally(self):
        with TestClient(create_app()) as client:
            assert client.get("/api/openapi.json").status_code == 200

    @pytest.mark.parametrize("secret", ["change-me-in-production", "too-short"])
    def test_refuses_to_start_without_a_real_secret(self, secret):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(app_env="production", secret_key=secret)

    def test_accepts_a_long_random_secret(self):
        settings = Settings(app_env="production", secret_key="x" * 32)
        assert settings.secret_key == "x" * 32
