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


# ── Request ID + logging middleware ───────────────────────────────────────────
class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Attach unique request ID to every request
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"| status={response.status_code} "
            f"| {duration:.1f}ms"
            f"| ip={request.client.host}"
        )

        # Attach request ID to response header
        response.headers["X-Request-ID"] = request_id
        return response


# ── Global exception handlers ──────────────────────────────────────────────────

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors cleanly."""
    errors = []
    for error in exc.errors():
        field = " → ".join(str(e) for e in error["loc"] if e != "body")
        errors.append({"field": field, "message": error["msg"]})

    logger.warning(f"Validation error | path={request.url.path} | errors={errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "errors": errors,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle unexpected DB errors without leaking details."""
    logger.error(f"Database error | path={request.url.path} | error={str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "A database error occurred. Please try again later.",
        },
    )


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit errors."""
    logger.warning(f"Rate limit exceeded | path={request.url.path} | ip={request.client.host}")

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "message": "Too many requests. Please slow down and try again.",
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — never expose raw errors to client."""
    logger.error(f"Unhandled error | path={request.url.path} | error={str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
        },
    )