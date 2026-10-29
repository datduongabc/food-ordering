"""Logs and error reporting.

Every request gets an id (nginx's, when it sent one) that appears on each log line written
while handling it and in the X-Request-ID response header, so a customer's report can be
matched to the logs. Production writes one JSON object per line for log tooling.
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar

import sentry_sdk
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings

REQUEST_ID_HEADER = "X-Request-ID"
# Polled every few seconds by the container health check; logging it would drown the rest.
QUIET_PATHS = frozenset({"/api/health"})
request_id: ContextVar[str] = ContextVar("request_id", default="-")

logger = logging.getLogger("app.requests")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


class JsonFormatter(logging.Formatter):
    # Attributes every LogRecord has; anything else was passed through `extra`.
    _STANDARD = frozenset(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {
        "message",
        "asctime",
        "request_id",
    }

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        entry |= {k: v for k, v in vars(record).items() if k not in self._STANDARD}
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


class _AppHandler(logging.StreamHandler):
    """Marks the handler this module installs, so configuring again replaces only it."""


def configure_logging(settings: Settings) -> None:
    handler = _AppHandler()
    handler.addFilter(_RequestIdFilter())
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
        )
    # On the root logger, so library warnings are formatted too; uvicorn keeps its own.
    root = logging.getLogger()
    root.handlers = [h for h in root.handlers if not isinstance(h, _AppHandler)] + [handler]
    logging.getLogger("app").setLevel(logging.INFO)


def init_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Request bodies hold passwords, codes and addresses; IPs and cookies are personal.
        send_default_pii=False,
        max_request_body_size="never",
    )


class RequestLogMiddleware:
    """One log line per request, with its id, outcome and duration."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in QUIET_PATHS:
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(REQUEST_ID_HEADER.lower().encode(), b"").decode()
        # Trust only a plausible id; anything else could be used to forge log lines.
        rid = incoming if incoming.isalnum() and len(incoming) <= 64 else uuid.uuid4().hex
        token = request_id.set(rid)
        sentry_sdk.set_tag("request_id", rid)
        started = time.perf_counter()
        status = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = rid
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            client = scope.get("client")
            logger.info(
                "%s %s %s",
                scope["method"],
                scope["path"],
                status,
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    "client_ip": client[0] if client else None,
                },
            )
            request_id.reset(token)
