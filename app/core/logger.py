# 📁 app/core/logger.py

import logging
import sys
from app.core.config import settings

# ── Log format ─────────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # ── Console handler ────────────────────────────────────────────────────────
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)

    return logger


# ── Module-level loggers ───────────────────────────────────────────────────────
logger = setup_logger("app")
auth_logger = setup_logger("app.auth")
db_logger = setup_logger("app.db")