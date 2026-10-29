from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.rate_limit import CODE_ENTRY, LOGIN, LOGIN_FAILURES
from app.modules.auth import service as auth_service
from app.modules.auth.models import UserSession
from app.modules.users.models import User
from tests.data import USER


def login(client: TestClient, email=USER["email"], password=USER["password"], **extra):
    return client.post("/api/auth/login", json={"email": email, "password": password, **extra})


class TestRegister:
    def test_creates_customer_without_logging_in(self, client):
        response = client.post("/api/auth/register", json=USER)

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == USER["email"]
        assert body["role"] == "CUSTOMER"
        assert body["is_email_verified"] is False
        assert "password" not in body and "password_hash" not in body
        assert client.get("/api/auth/me").status_code == 401

    def test_normalises_email_case(self, client):
        response = client.post("/api/auth/register", json={**USER, "email": "A@Example.COM"})
        assert response.json()["email"] == "a@example.com"

    def test_rejects_duplicate_email(self, client, registered_user):
        response = client.post("/api/auth/register", json={**USER, "phone": "0999999999"})
        assert response.status_code == 409
        assert response.json()["code"] == "email_taken"

    def test_rejects_duplicate_phone(self, client, registered_user):
        response = client.post("/api/auth/register", json={**USER, "email": "b@example.com"})
        assert response.status_code == 409
        assert response.json()["code"] == "phone_taken"

    def test_rejects_invalid_payload_with_422(self, client):
        response = client.post("/api/auth/register", json={**USER, "password": "short"})
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"
        assert response.json()["detail"][0]["loc"] == ["body", "password"]


class TestLogin:
    def test_sets_httponly_session_cookie(self, client, registered_user):
        response = login(client)

        assert response.status_code == 200
        set_cookie = response.headers["set-cookie"]
        assert get_settings().session_cookie_name in set_cookie
        assert "HttpOnly" in set_cookie
        assert "Max-Age" not in set_cookie  # browser-session cookie without "remember me"
        assert client.get("/api/auth/me").json()["email"] == USER["email"]

    def test_remember_me_sets_persistent_cookie(self, client, registered_user):
        response = login(client, remember=True)
        assert "Max-Age=604800" in response.headers["set-cookie"]

    def test_wrong_password_and_unknown_email_look_identical(self, client, registered_user):
        wrong_password = login(client, password="wrong-password")
        unknown_email = login(client, email="nobody@example.com")

        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.json() == unknown_email.json()

    def test_blocks_repeated_failures_the_same_way_for_unknown_emails(
        self, client, registered_user
    ):
        def blocked_after_failures(email):
            # Both runs together pass the per-address cap on sign-in attempts; keep it out.
            client.app.state.rate_limiter.forget(LOGIN, "ip:testclient")
            for _ in range(LOGIN_FAILURES.requests):
                assert login(client, email=email, password="wrong-password").status_code == 401
            return login(client, email=email, password=USER["password"])

        real = blocked_after_failures(USER["email"])
        unknown = blocked_after_failures("nobody@example.com")

        assert real.status_code == unknown.status_code == 429
        assert real.json()["code"] == unknown.json()["code"] == "rate_limited"

    def test_success_clears_earlier_failures(self, client, registered_user):
        for _ in range(LOGIN_FAILURES.requests - 1):
            login(client, password="wrong-password")
        assert login(client).status_code == 200

        for _ in range(LOGIN_FAILURES.requests - 1):
            assert login(client, password="wrong-password").status_code == 401

    def test_failures_still_count_with_rate_limits_off(self, client, registered_user, monkeypatch):
        monkeypatch.setattr(get_settings(), "rate_limits_enabled", False)
        for _ in range(LOGIN_FAILURES.requests):
            login(client, password="wrong-password")
        assert login(client).status_code == 429

    def test_deactivated_user_cannot_login_and_loses_sessions(self, client, registered_user, db):
        login(client)
        user = db.scalar(select(User).where(User.email == USER["email"]))
        user.deleted_at = utcnow()
        db.commit()

        assert client.get("/api/auth/me").status_code == 401
        assert login(client).status_code == 401

    def test_expired_session_is_rejected(self, logged_in_client, db):
        user_session = db.scalar(select(UserSession))
        user_session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()

        assert logged_in_client.get("/api/auth/me").status_code == 401


class TestLogout:
    def test_revokes_server_session(self, logged_in_client, db):
        response = logged_in_client.post("/api/auth/logout")

        assert response.status_code == 204
        assert logged_in_client.get("/api/auth/me").status_code == 401
        assert db.scalar(select(UserSession)) is None


class TestCsrf:
    def test_post_without_header_is_rejected(self, client):
        del client.headers["X-CSRF-Token"]
        response = client.post("/api/auth/register", json=USER)
        assert response.status_code == 403

    def test_post_with_wrong_token_is_rejected(self, client):
        client.headers["X-CSRF-Token"] = "forged"
        assert client.post("/api/auth/register", json=USER).status_code == 403


class TestPasswordReset:
    def test_full_reset_flow_revokes_existing_sessions(self, logged_in_client, outbox):
        client = logged_in_client
        response = client.post("/api/auth/password/forgot", json={"email": USER["email"]})
        assert response.status_code == 202

        code = outbox.last_code()
        response = client.post(
            "/api/auth/password/reset",
            json={"email": USER["email"], "code": code, "new_password": "brand-new-pass"},
        )

        assert response.status_code == 204
        assert client.get("/api/auth/me").status_code == 401
        assert login(client).status_code == 401
        assert login(client, password="brand-new-pass").status_code == 200

    def test_unknown_email_gets_same_response_and_no_mail(self, client, registered_user, outbox):
        known = client.post("/api/auth/password/forgot", json={"email": USER["email"]})
        unknown = client.post("/api/auth/password/forgot", json={"email": "x@example.com"})

        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json()
        assert len(outbox.sent) == 1

    def test_code_is_single_use(self, client, registered_user, outbox):
        client.post("/api/auth/password/forgot", json={"email": USER["email"]})
        payload = {"email": USER["email"], "code": outbox.last_code(), "new_password": "pass-one-1"}

        assert client.post("/api/auth/password/reset", json=payload).status_code == 204
        assert client.post("/api/auth/password/reset", json=payload).status_code == 400

    def test_new_code_invalidates_previous_one(self, client, registered_user, monkeypatch):
        codes = iter(["111111", "222222"])
        monkeypatch.setattr(auth_service, "new_otp_code", lambda: next(codes))
        client.post("/api/auth/password/forgot", json={"email": USER["email"]})
        client.post("/api/auth/password/forgot", json={"email": USER["email"]})

        payload = {"email": USER["email"], "new_password": "whatever-1"}
        stale = client.post("/api/auth/password/reset", json={**payload, "code": "111111"})
        fresh = client.post("/api/auth/password/reset", json={**payload, "code": "222222"})

        assert stale.status_code == 400
        assert fresh.status_code == 204

    def test_blocks_after_max_wrong_codes(self, client, registered_user, outbox):
        client.post("/api/auth/password/forgot", json={"email": USER["email"]})
        real_code = outbox.last_code()
        wrong_code = "000000" if real_code != "000000" else "111111"
        payload = {"email": USER["email"], "new_password": "new-password-1"}

        for _ in range(get_settings().otp_max_attempts):
            response = client.post("/api/auth/password/reset", json={**payload, "code": wrong_code})
            assert response.status_code == 400

        blocked = client.post("/api/auth/password/reset", json={**payload, "code": real_code})
        assert blocked.status_code == 429

    def test_unknown_email_blocks_after_max_wrong_codes_like_a_real_one(self, client):
        email = "nobody@example.com"
        client.post("/api/auth/password/forgot", json={"email": email})
        payload = {"email": email, "code": "000000", "new_password": "new-password-1"}

        for _ in range(get_settings().otp_max_attempts):
            response = client.post("/api/auth/password/reset", json=payload)
            assert response.status_code == 400
            assert response.json()["code"] == "invalid_code"

        blocked = client.post("/api/auth/password/reset", json=payload)
        assert blocked.status_code == 429
        assert blocked.json()["code"] == "too_many_code_attempts"

        # A new request starts a fresh code, as it would for a real account.
        client.post("/api/auth/password/forgot", json={"email": email})
        assert client.post("/api/auth/password/reset", json=payload).json()["code"] == (
            "invalid_code"
        )

    def test_without_a_request_any_email_only_ever_hears_invalid_code(
        self, client, registered_user
    ):
        for email in (USER["email"], "nobody@example.com"):
            client.app.state.rate_limiter.forget(CODE_ENTRY, "ip:testclient")
            payload = {"email": email, "code": "000000", "new_password": "new-password-1"}
            for _ in range(get_settings().otp_max_attempts + 1):
                response = client.post("/api/auth/password/reset", json=payload)
                assert response.json()["code"] == "invalid_code"


class TestChangePassword:
    def test_keeps_current_session_and_revokes_others(self, logged_in_client, db):
        user = db.scalar(select(User).where(User.email == USER["email"]))
        auth_service.create_session(db, user, remember=True)  # another device
        assert db.query(UserSession).count() == 2

        response = logged_in_client.post(
            "/api/auth/password/change",
            json={"current_password": USER["password"], "new_password": "changed-pass-1"},
        )

        assert response.status_code == 204
        assert logged_in_client.get("/api/auth/me").status_code == 200
        assert db.query(UserSession).count() == 1

    def test_rejects_wrong_current_password(self, logged_in_client):
        response = logged_in_client.post(
            "/api/auth/password/change",
            json={"current_password": "not-my-password", "new_password": "changed-pass-1"},
        )
        assert response.status_code == 400

    def test_requires_login(self, client):
        response = client.post(
            "/api/auth/password/change",
            json={"current_password": "whatever-1", "new_password": "changed-pass-1"},
        )
        assert response.status_code == 401


class TestEmailVerification:
    def test_verifies_with_emailed_code(self, logged_in_client, outbox):
        assert logged_in_client.post("/api/auth/email/verification").status_code == 202

        response = logged_in_client.post(
            "/api/auth/email/verify", json={"code": outbox.last_code()}
        )

        assert response.status_code == 200
        assert response.json()["is_email_verified"] is True
        assert logged_in_client.post("/api/auth/email/verification").status_code == 400

    def test_wrong_code_fails(self, logged_in_client, outbox):
        logged_in_client.post("/api/auth/email/verification")
        wrong = "000000" if outbox.last_code() != "000000" else "111111"
        response = logged_in_client.post("/api/auth/email/verify", json={"code": wrong})
        assert response.status_code == 400
