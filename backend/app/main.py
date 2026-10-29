from fastapi import FastAPI

from app.core.csrf import CSRFMiddleware
from app.core.errors import register_error_handlers
from app.modules.auth.router import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="DaTeNO Restaurant API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(CSRFMiddleware)
    register_error_handlers(app)

    app.include_router(auth_router, prefix="/api")

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
