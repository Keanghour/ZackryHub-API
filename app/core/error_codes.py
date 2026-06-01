# 📁 app/core/error_codes.py

# ── Auth ───────────────────────────────────────────────────────────────────────
AUTH_UNAUTHORIZED          = "AUTH_401"
AUTH_FORBIDDEN             = "AUTH_403"
AUTH_INVALID_TOKEN         = "AUTH_TOKEN_INVALID"
AUTH_EXPIRED_TOKEN         = "AUTH_TOKEN_EXPIRED"
AUTH_INVALID_CREDENTIALS   = "AUTH_INVALID_CREDENTIALS"
AUTH_ACCOUNT_DEACTIVATED   = "AUTH_ACCOUNT_DEACTIVATED"
AUTH_EMAIL_EXISTS          = "AUTH_EMAIL_EXISTS"
AUTH_INVALID_RESET_TOKEN   = "AUTH_RESET_TOKEN_INVALID"
AUTH_RESET_TOKEN_EXPIRED   = "AUTH_RESET_TOKEN_EXPIRED"
AUTH_WRONG_PASSWORD        = "AUTH_WRONG_PASSWORD"

# ── Validation ─────────────────────────────────────────────────────────────────
VALIDATION_ERROR           = "VALIDATION_422"

# ── Resource ───────────────────────────────────────────────────────────────────
RESOURCE_NOT_FOUND         = "RESOURCE_404"
RESOURCE_CONFLICT          = "RESOURCE_409"

# ── Order ──────────────────────────────────────────────────────────────────────
ORDER_INVALID_STATUS       = "ORDER_INVALID_STATUS"
ORDER_INSUFFICIENT_STOCK   = "ORDER_INSUFFICIENT_STOCK"
ORDER_CANCELLED            = "ORDER_CANCELLED"

# ── Inventory ──────────────────────────────────────────────────────────────────
INVENTORY_INSUFFICIENT_STOCK = "INVENTORY_INSUFFICIENT_STOCK"

# ── Server ─────────────────────────────────────────────────────────────────────
SERVER_ERROR               = "SERVER_500"
DB_ERROR                   = "DB_500"

# ── Rate limit ─────────────────────────────────────────────────────────────────
RATE_LIMIT_EXCEEDED        = "RATE_LIMIT_429"