from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware
from app.core.errors import register_error_handlers
from app.core.headers import SecurityHeadersMiddleware
from app.core.observability import RequestLogMiddleware, configure_logging, init_sentry
from app.core.rate_limit import RateLimiter, RateLimitMiddleware
from app.modules.admin.router import router as admin_router
from app.modules.auth.phantom import PhantomResetCodes
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
    app.state.rate_limiter = RateLimiter()
    app.state.phantom_reset_codes = PhantomResetCodes()
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

    return app


app = create_app()
