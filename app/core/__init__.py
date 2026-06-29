# 📁 app/core/__init__.py

from . import error_codes
from .config import settings
from .database import engine
from .logger import logger, auth_logger, db_logger
from .limiter import limiter
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from .middleware import (
    RequestMiddleware,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    rate_limit_exception_handler,
    global_exception_handler,
)
from .logging_middleware import LoggingMiddleware
from .security_middleware import SecurityMiddleware
from .dependencies import get_current_user, require_roles
from .seeder import seed_roles_and_permissions
from .exceptions import InsufficientStockException, AppException


routes_cores = {
    "settings":   settings,
    "engine":     engine,
    "limiter":    limiter,
    "seed":       seed_roles_and_permissions,
    "middleware":  RequestMiddleware,
    "exception_handlers": {
        "validation": validation_exception_handler,
        "sqlalchemy": sqlalchemy_exception_handler,
        "rate_limit": rate_limit_exception_handler,
        "global":     global_exception_handler,
    },
}