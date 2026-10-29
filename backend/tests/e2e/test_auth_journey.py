"""Full customer account journeys against a real server process over HTTP."""

import uuid

import pytest


@pytest.fixture
def customer() -> dict:
    # The server is shared by the whole session, so every test gets its own account.
    suffix = uuid.uuid4().hex[:8]
    return {
        "name": "Tran Thi B",
        "email": f"b-{suffix}@example.com",
        "password": "first-password",
        "phone": f"09{int(suffix, 16) % 10**8:08d}",
    }


def test_register_verify_email_and_sign_out(server, customer):
    browser = server.client()

    assert browser.post("/api/auth/register", json=customer).status_code == 201
    login = browser.post(
        "/api/auth/login",
        json={"email": customer["email"], "password": customer["password"], "remember": True},
    )
    assert login.status_code == 200
    session_cookie = next(
        header for header in login.headers.get_list("set-cookie") if "dateno_session" in header
    )
    assert "HttpOnly" in session_cookie and "SameSite=lax" in session_cookie

    assert browser.post("/api/auth/email/verification").status_code == 202
    code = server.last_emailed_code(customer["email"])
    verified = browser.post("/api/auth/email/verify", json={"code": code})
    assert verified.json()["is_email_verified"] is True

    assert browser.post("/api/auth/logout").status_code == 204
    assert browser.get("/api/auth/me").status_code == 401


def test_forgot_password_signs_out_other_devices(server, customer):
    laptop, phone = server.client(), server.client()
    assert laptop.post("/api/auth/register", json=customer).status_code == 201
    credentials = {"email": customer["email"], "password": customer["password"]}
    assert laptop.post("/api/auth/login", json=credentials).status_code == 200
    assert phone.post("/api/auth/login", json=credentials).status_code == 200

    assert (
        phone.post("/api/auth/password/forgot", json={"email": customer["email"]}).status_code
        == 202
    )
    reset = phone.post(
        "/api/auth/password/reset",
        json={
            "email": customer["email"],
            "code": server.last_emailed_code(customer["email"]),
            "new_password": "second-password",
        },
    )
    assert reset.status_code == 204

    assert laptop.get("/api/auth/me").status_code == 401
    assert phone.post("/api/auth/login", json=credentials).status_code == 401
    new_login = phone.post("/api/auth/login", json={**credentials, "password": "second-password"})
    assert new_login.status_code == 200


def test_cross_site_post_without_csrf_header_is_blocked(server, customer):
    browser = server.client()
    del browser.headers["X-CSRF-Token"]

    response = browser.post("/api/auth/register", json=customer)

    assert response.status_code == 403
