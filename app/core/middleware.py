# 📁 app/core/middleware.py

import uuid
import time
import json
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.logger import logger
from app.core import error_codes


def error_response(status_code: int, message: str, error_messages: str) -> dict:
    """Standard error response format."""
    return {
        "success":        False,
        "code":           status_code,
        "message":        message,
        "error_messages": error_messages,
    }


# ── Request ID + logging + dynamic `code` sync middleware ─────────────────────
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

        # ── Sync `code` field in JSON body with actual HTTP status_code ────────
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type and hasattr(response, "body"):
            try:
                body = json.loads(response.body)
                if isinstance(body, dict) and "code" in body:
                    if body.get("code") != response.status_code:
                        body["code"] = response.status_code
                        new_body = json.dumps(body).encode("utf-8")
                        response.body = new_body
                        response.headers["content-length"] = str(len(new_body))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # not JSON or not decodable — skip

        return response


# ── HTTP exception handler ─────────────────────────────────────────────────────
async def http_exception_handler(request: Request, exc) -> JSONResponse:
    if isinstance(exc.detail, dict):
        # Sync code with actual status_code too
        detail = {**exc.detail, "code": exc.status_code}
        return JSONResponse(status_code=exc.status_code, content=detail)

    code_map = {
        400: error_codes.VALIDATION_ERROR,
        401: error_codes.AUTH_UNAUTHORIZED,
        403: error_codes.AUTH_FORBIDDEN,
        404: error_codes.RESOURCE_NOT_FOUND,
        409: error_codes.RESOURCE_CONFLICT,
        413: error_codes.REQUEST_TOO_LARGE,
        429: error_codes.RATE_LIMIT_EXCEEDED,
        500: error_codes.SERVER_ERROR,
    }
    error_messages = code_map.get(exc.status_code, f"HTTP_ERROR_{exc.status_code}")

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail, error_messages),
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
            **error_response(422, "Validation error", error_codes.VALIDATION_ERROR),
            "errors": errors,
        },
    )


# ── SQLAlchemy error handler ───────────────────────────────────────────────────
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"Database error | path={request.url.path} | error={str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(500, "A database error occurred. Please try again later.", error_codes.DB_ERROR),
    )


# ── Rate limit handler ─────────────────────────────────────────────────────────
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning(f"Rate limit exceeded | path={request.url.path} | ip={request.client.host}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response(429, "Too many requests. Please slow down and try again.", error_codes.RATE_LIMIT_EXCEEDED),
    )


# ── Global catch-all handler ───────────────────────────────────────────────────
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error | path={request.url.path} | error={str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(500, "An unexpected error occurred. Please try again later.", error_codes.SERVER_ERROR),
    )