# 📁 app/core/logging_middleware.py

import json
import time
import secrets
import logging
import traceback
from datetime import datetime, UTC

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


# ── Logger config ──────────────────────────────────────────────────────────────
logger = logging.getLogger("api_logs")

handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


# ── Skip logging for these paths (health check, docs) ─────────────────────────
SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


# ── Log helper ─────────────────────────────────────────────────────────────────
class LogHelper:

    @staticmethod
    def now() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def trace_id() -> str:
        return (
            f"{secrets.token_hex(4)}-"
            f"{secrets.token_hex(8)}-"
            f"{secrets.token_hex(5)}"
        )

    @staticmethod
    def safe_json(data):
        try:
            return json.loads(json.dumps(data, ensure_ascii=False))
        except Exception:
            return str(data)

    @staticmethod
    def mask(data: dict) -> dict:
        """Mask sensitive fields so they never appear in logs."""
        if not isinstance(data, dict):
            return data

        sensitive_keys = {
            "password",
            "new_password",
            "current_password",
            "token",
            "access_token",
            "refresh_token",
            "reset_token",
            "secret",
            "secret_key",
            "authorization",
        }

        return {
            k: ("***" if k.lower() in sensitive_keys else v)
            for k, v in data.items()
        }

    @classmethod
    def log(cls, level: int, payload: dict) -> None:
        payload["timestamp"] = cls.now()
        payload["app"]       = settings.APP_NAME
        payload["env"]       = settings.ENVIRONMENT
        logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))


# ── Enterprise logging middleware ──────────────────────────────────────────────
class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        # Skip noisy paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        trace_id      = LogHelper.trace_id()
        method        = request.method
        path          = request.url.path
        query_params  = str(request.query_params) if request.query_params else None

        # Get real IP (handles proxies / load balancers)
        ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else "unknown")
        )

        # Get endpoint function name
        endpoint      = request.scope.get("endpoint")
        endpoint_name = endpoint.__name__ if endpoint else "unknown"

        # ── Read + mask request body ───────────────────────────────────────────
        try:
            raw  = await request.body()
            body = json.loads(raw.decode()) if raw else {}
        except Exception:
            body = {}

        body = LogHelper.mask(body)

        start = time.perf_counter()

        # ── Log incoming request ───────────────────────────────────────────────
        LogHelper.log(
            logging.INFO,
            {
                "type":          "request",
                "trace_id":      trace_id,
                "method":        method,
                "path":          path,
                "query_params":  query_params,
                "endpoint":      endpoint_name,
                "ip":            ip,
                "user_agent":    request.headers.get("user-agent"),
                "body":          body,
            }
        )

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)

            # ── Capture response body ──────────────────────────────────────────
            resp_body_bytes = b""
            async for chunk in response.body_iterator:
                resp_body_bytes += chunk

            try:
                response_body = json.loads(resp_body_bytes.decode())
            except Exception:
                response_body = resp_body_bytes.decode()

            response_body = LogHelper.mask(response_body) if isinstance(response_body, dict) else response_body

            # ── Rebuild response (required after reading body_iterator) ─────────
            response = Response(
                content=resp_body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            # ── Inject trace ID into response header ───────────────────────────
            response.headers["X-Trace-Id"] = trace_id

            # ── Log response ───────────────────────────────────────────────────
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO

            LogHelper.log(
                logging.INFO,
                {
                    "type":        "response",
                    "trace_id":    trace_id,
                    "method":      method,
                    "path":        path,
                    "status":      response.status_code,
                    "duration_ms": duration_ms,
                    "endpoint":    endpoint_name,
                    "response":    response_body,
                }
            )

            # ── Full trace log (request + response combined) ───────────────────
            LogHelper.log(
                log_level,
                {
                    "type":        "full",
                    "trace_id":    trace_id,
                    "method":      method,
                    "path":        path,
                    "query_params": query_params,
                    "endpoint":    endpoint_name,
                    "ip":          ip,
                    "status":      response.status_code,
                    "duration_ms": duration_ms,
                    "request":     body,
                    "response":    response_body,
                }
            )

            return response

        except Exception as ex:
            duration_ms = int((time.perf_counter() - start) * 1000)

            # ── Extract error location ─────────────────────────────────────────
            tb = traceback.extract_tb(ex.__traceback__)
            if tb:
                f        = tb[-1]
                location = f"{f.filename.split('/')[-1]}:{f.name}:{f.lineno}"
            else:
                location = "unknown"

            LogHelper.log(
                logging.ERROR,
                {
                    "type":          "error",
                    "trace_id":      trace_id,
                    "method":        method,
                    "path":          path,
                    "endpoint":      endpoint_name,
                    "ip":            ip,
                    "duration_ms":   duration_ms,
                    "location":      location,
                    "error_type":    type(ex).__name__,
                    "error_message": str(ex),
                    "request":       body,
                }
            )

            raise