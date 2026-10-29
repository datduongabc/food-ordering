from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware
from app.core.errors import register_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.catalog.router import router as catalog_router
from app.modules.feedback.router import router as feedback_router
from app.modules.orders.router import router as orders_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DaTeNO Restaurant API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(CSRFMiddleware)
    register_error_handlers(app)

    app.include_router(auth_router, prefix="/api")
    app.include_router(catalog_router, prefix="/api")
    app.include_router(feedback_router, prefix="/api")
    app.include_router(cart_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")
    app.mount(settings.media_url, StaticFiles(directory=settings.media_dir), name="media")

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
