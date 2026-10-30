from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError

VALIDATION_ERROR = "validation_error"


def error_body(detail: Any, code: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"detail": detail, "code": code, "params": params or {}}


class AppError(Exception):
    """Domain error raised by services and converted to a JSON body so routers stay thin.

    `detail` is an English sentence for API users and logs. The SPA shows a translation of
    `code` (filled in from `params`) instead, so a Vietnamese page never shows English text.
    """

    status_code = 400

    def __init__(
        self,
        detail: str,
        *,
        code: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.params = params or {}
        self.headers = headers


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class TooManyRequestsError(AppError):
    status_code = 429


class ServiceUnavailableError(AppError):
    status_code = 503


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(error_body(exc.detail, exc.code, exc.params)),
            headers=exc.headers,
        )

    async def handle_out_of_range(_: Request, exc: Exception) -> JSONResponse:
        # A value the database cannot hold, such as an id past the integer range: the
        # request is wrong, not the server. Postgres reports it as a DataError; SQLite's
        # driver raises OverflowError before the query runs.
        return JSONResponse(
            status_code=400,
            content=error_body("A value in the request is out of range.", "value_out_of_range"),
        )

    app.add_exception_handler(DataError, handle_out_of_range)
    app.add_exception_handler(OverflowError, handle_out_of_range)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Same shape as FastAPI's default, plus the code every other error carries.
        return JSONResponse(
            status_code=422, content=jsonable_encoder(error_body(exc.errors(), VALIDATION_ERROR))
        )
