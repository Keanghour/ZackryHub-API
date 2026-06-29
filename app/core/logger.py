# # 📁 app/core/logger.py

# import logging
# import sys
# from app.core.config import settings

# LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
# DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# def setup_logger(name: str) -> logging.Logger:
#     logger = logging.getLogger(name)
#     if logger.handlers:
#         return logger
#     logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
#     handler = logging.StreamHandler(sys.stdout)
#     handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
#     logger.addHandler(handler)
#     logger.propagate = False   # prevent duplicate logs bubbling up
#     return logger


# # ── Silence noisy third-party loggers ─────────────────────────────────────────
# logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)   # hide SQL logs
# logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
# logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
# logging.getLogger("uvicorn.access").setLevel(logging.WARNING)      # hide uvicorn access logs (we have our own)


# # ── App loggers ────────────────────────────────────────────────────────────────
# logger      = setup_logger("app")
# auth_logger = setup_logger("app.auth")
# db_logger   = setup_logger("app.db")


# 📁 app/core/logger.py

import logging
import sys
from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)
    logger.propagate = False   # prevent duplicate logs bubbling up
    return logger


# ── Silence ALL third-party + internal module loggers ─────────────────────────
SILENCED_LOGGERS = [
    # SQLAlchemy
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.dialects",
    "sqlalchemy.orm",

    # Uvicorn
    "uvicorn.access",
    "uvicorn.error",

    # App internal module loggers (handled by LoggingMiddleware instead)
    "app.auth",
    "app.db",
    "app.product",
    "app.order",
    "app.inventory",
    "app.warehouse",
    "app.category",
    "app.user",
    "app.role",
    "app.dashboard",
    "app.seeder",
]

for name in SILENCED_LOGGERS:
    logging.getLogger(name).setLevel(logging.CRITICAL)  # effectively silent
    logging.getLogger(name).propagate = False


# ── Active app loggers (startup + critical only) ───────────────────────────────
logger      = setup_logger("app")         # startup, shutdown, critical errors
auth_logger = setup_logger("app.auth")    # keep but silence above ↑
db_logger   = setup_logger("app.db")      # keep but silence above ↑