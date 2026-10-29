import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware

COOKIE = get_settings().csrf_cookie_name


async def ok(_request):
    return PlainTextResponse("ok")


@pytest.fixture
def client() -> TestClient:
    app = Starlette(
        routes=[
            Route("/action", ok, methods=["GET", "POST"]),
            Route("/webhook", ok, methods=["POST"]),
        ]
    )
    app.add_middleware(CSRFMiddleware, exempt_paths=frozenset({"/webhook"}))
    return TestClient(app)


def test_safe_request_issues_readable_cookie(client):
    response = client.get("/action")

    assert response.status_code == 200
    set_cookie = response.headers["set-cookie"]
    assert set_cookie.startswith(f"{COOKIE}=")
    assert "HttpOnly" not in set_cookie  # the SPA must be able to read it
    assert "SameSite=Lax" in set_cookie


def test_existing_cookie_is_not_reissued(client):
    client.get("/action")
    assert "set-cookie" not in client.get("/action").headers


def test_post_with_matching_header_passes(client):
    client.get("/action")
    token = client.cookies[COOKIE]

    assert client.post("/action", headers={"X-CSRF-Token": token}).status_code == 200


@pytest.mark.parametrize("headers", [{}, {"X-CSRF-Token": "forged"}])
def test_post_without_valid_header_is_rejected(client, headers):
    client.get("/action")
    assert client.post("/action", headers=headers).status_code == 403


def test_post_without_cookie_is_rejected_even_with_header(client):
    assert client.post("/action", headers={"X-CSRF-Token": "anything"}).status_code == 403


def test_exempt_path_skips_check(client):
    # Server-to-server callbacks (e.g. payment webhooks) cannot carry the browser cookie.
    assert client.post("/webhook").status_code == 200
