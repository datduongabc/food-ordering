from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from app.core.cache import build_catalog_cache
from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware
from app.core.deps import DbSession
from app.core.errors import register_error_handlers
from app.core.events import build_event_broker
from app.core.headers import SecurityHeadersMiddleware
from app.core.idempotency import build_idempotency_store
from app.core.metrics import check_readiness, render_prometheus
from app.core.observability import RequestLogMiddleware, configure_logging, init_sentry
from app.core.rate_limit import RateLimitMiddleware, build_rate_limiter
from app.modules.admin.router import router as admin_router
from app.modules.auth.phantom import build_phantom_reset_codes
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import router as catalog_router
from app.modules.feedback.router import router as feedback_router
from app.modules.orders.router import router as orders_router
from app.modules.promotions.router import router as promotions_router
from app.modules.reservations.router import router as reservations_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    init_sentry(settings)
    app = FastAPI(
        title="DaTeNO Restaurant API",
        version="0.1.0",
        # The schema maps every endpoint; publish it only where developers need it.
        docs_url="/api/docs" if settings.is_local else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.is_local else None,
    )
    app.state.rate_limiter = build_rate_limiter(settings)
    app.state.phantom_reset_codes = build_phantom_reset_codes(settings)
    app.state.catalog_cache = build_catalog_cache(settings)
    app.state.idempotency_store = build_idempotency_store(settings)
    app.state.event_broker = build_event_broker(settings)
    # Added last runs first: every request is logged, headers wrap every response, and floods
    # are refused before CSRF checks.
    # MoMo posts payment results server to server; they carry a signature instead of a token.
    app.add_middleware(CSRFMiddleware, exempt_paths=frozenset({"/api/payments/momo/ipn"}))
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLogMiddleware)
    register_error_handlers(app)

    app.include_router(auth_router, prefix="/api")
    app.include_router(catalog_router, prefix="/api")
    app.include_router(feedback_router, prefix="/api")
    app.include_router(cart_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")
    app.include_router(promotions_router, prefix="/api")
    app.include_router(reservations_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.mount(settings.media_url, StaticFiles(directory=settings.media_dir), name="media")

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health/ready", tags=["meta"])
    def health_ready(request: Request, db: DbSession, response: Response) -> dict[str, Any]:
        report = check_readiness(request.app, db)
        if report["status"] != "ok":
            response.status_code = 503
        return report

    @app.get("/api/metrics", tags=["meta"], response_class=Response)
    def metrics(request: Request, db: DbSession) -> Response:
        body = render_prometheus(request.app, db)
        return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")

    return app


app = create_app()
