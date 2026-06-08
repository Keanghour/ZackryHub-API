# 📁 app/core/security_middleware.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.core import error_codes


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Adds:
    1. Security headers (HSTS, XSS, clickjacking protection etc.)
    2. Request body size limit
    """

    async def dispatch(self, request: Request, call_next):

        # ── 1. Block oversized request bodies ─────────────────────────────────
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_BODY_SIZE:
            logger.warning(
                f"Request body too large | "
                f"size={content_length} "
                f"max={settings.MAX_REQUEST_BODY_SIZE} "
                f"path={request.url.path} "
                f"ip={request.client.host}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success":    False,
                    "message":    f"Request body too large. Max allowed: {settings.MAX_REQUEST_BODY_SIZE // (1024*1024)}MB",
                    "error_code": "REQUEST_TOO_LARGE",
                },
            )

        response = await call_next(request)

        # ── 2. Add security headers ────────────────────────────────────────────
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"]             = "no-store"

        # Only add HSTS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response