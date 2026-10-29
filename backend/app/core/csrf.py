import hmac
import secrets

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import get_settings

CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware:
    """Double-submit cookie protection for cookie-authenticated API calls.

    The SPA reads the non-httpOnly CSRF cookie and echoes it in a header; a
    cross-site form can send the cookie but cannot read it to set the header.
    """

    def __init__(self, app: ASGIApp, exempt_paths: frozenset[str] = frozenset()):
        self.app = app
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        request = Request(scope)
        cookie_token = request.cookies.get(settings.csrf_cookie_name)

        if request.method not in SAFE_METHODS and request.url.path not in self.exempt_paths:
            header_token = request.headers.get(CSRF_HEADER)
            if (
                not cookie_token
                or not header_token
                or not hmac.compare_digest(cookie_token, header_token)
            ):
                response = JSONResponse(
                    {"detail": "CSRF token missing or invalid. Reload the page and try again."},
                    status_code=403,
                )
                await response(scope, receive, send)
                return

        if cookie_token:
            await self.app(scope, receive, send)
            return

        new_token = secrets.token_urlsafe(32)

        async def send_with_cookie(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                secure = "" if settings.is_local else "; Secure"
                headers.append(
                    "set-cookie",
                    f"{settings.csrf_cookie_name}={new_token}; Path=/; SameSite=Lax{secure}",
                )
            await send(message)

        await self.app(scope, receive, send_with_cookie)
