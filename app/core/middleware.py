# 📁 app/core/middleware.py

import uuid
import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.logger import logger
from app.core import error_codes


# ── Request ID + logging middleware ───────────────────────────────────────────
class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"| status={response.status_code} "
            f"| {duration:.1f}ms "
            f"| ip={request.client.host}"
        )
        response.headers["X-Request-ID"] = request_id
        return response


# ── HTTP exception handler (handles dict detail + adds error_code) ─────────────
async def http_exception_handler(request: Request, exc) -> JSONResponse:
    if isinstance(exc.detail, dict):
        # Already a structured dict — return as-is (e.g. InsufficientStockException)
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    # Map status code to error_code
    code_map = {
        401: error_codes.AUTH_UNAUTHORIZED,
        403: error_codes.AUTH_FORBIDDEN,
        404: error_codes.RESOURCE_NOT_FOUND,
        409: error_codes.RESOURCE_CONFLICT,
        429: error_codes.RATE_LIMIT_EXCEEDED,
        500: error_codes.SERVER_ERROR,
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success":    False,
            "message":    exc.detail,
            "error_code": error_code,
        },
    )


# ── Validation error handler ───────────────────────────────────────────────────
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field = " → ".join(str(e) for e in error["loc"] if e != "body")
        errors.append({"field": field, "message": error["msg"]})

    logger.warning(f"Validation error | path={request.url.path} | errors={errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success":    False,
            "message":    "Validation error",
            "error_code": error_codes.VALIDATION_ERROR,
            "errors":     errors,
        },
    )


# ── SQLAlchemy error handler ───────────────────────────────────────────────────
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"Database error | path={request.url.path} | error={str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success":    False,
            "message":    "A database error occurred. Please try again later.",
            "error_code": error_codes.DB_ERROR,
        },
    )


# ── Rate limit handler ─────────────────────────────────────────────────────────
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(f"Rate limit exceeded | path={request.url.path} | ip={request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success":    False,
            "message":    "Too many requests. Please slow down and try again.",
            "error_code": error_codes.RATE_LIMIT_EXCEEDED,
        },
    )


# ── Global catch-all handler ───────────────────────────────────────────────────
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error | path={request.url.path} | error={str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success":    False,
            "message":    "An unexpected error occurred. Please try again later.",
            "error_code": error_codes.SERVER_ERROR,
        },
    )