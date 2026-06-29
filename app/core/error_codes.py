# 📁 app/core/error_codes.py

# ── Auth ───────────────────────────────────────────────────────────────────────
AUTH_UNAUTHORIZED          = "AUTH_UNAUTHORIZED"
AUTH_FORBIDDEN             = "AUTH_FORBIDDEN"
AUTH_INVALID_TOKEN         = "AUTH_INVALID_TOKEN"
AUTH_EXPIRED_TOKEN         = "AUTH_EXPIRED_TOKEN"
AUTH_INVALID_CREDENTIALS   = "AUTH_INVALID_CREDENTIALS"
AUTH_ACCOUNT_DEACTIVATED   = "AUTH_ACCOUNT_DEACTIVATED"
AUTH_EMAIL_EXISTS          = "AUTH_EMAIL_EXISTS"
AUTH_EMAIL_NOT_VERIFIED    = "AUTH_EMAIL_NOT_VERIFIED"
AUTH_INVALID_RESET_TOKEN   = "AUTH_INVALID_RESET_TOKEN"
AUTH_RESET_TOKEN_EXPIRED   = "AUTH_RESET_TOKEN_EXPIRED"
AUTH_WRONG_PASSWORD        = "AUTH_WRONG_PASSWORD"
AUTH_ACCOUNT_LOCKED        = "AUTH_ACCOUNT_LOCKED"

# ── Validation ─────────────────────────────────────────────────────────────────
VALIDATION_ERROR           = "VALIDATION_ERROR"

# ── Resource ───────────────────────────────────────────────────────────────────
RESOURCE_NOT_FOUND         = "RESOURCE_NOT_FOUND"
RESOURCE_CONFLICT          = "RESOURCE_CONFLICT"
REQUEST_TOO_LARGE          = "REQUEST_TOO_LARGE"

# ── Order ──────────────────────────────────────────────────────────────────────
ORDER_INVALID_STATUS       = "ORDER_INVALID_STATUS"
ORDER_INSUFFICIENT_STOCK   = "ORDER_INSUFFICIENT_STOCK"
ORDER_CANCELLED            = "ORDER_CANCELLED"

# ── Inventory ──────────────────────────────────────────────────────────────────
INVENTORY_INSUFFICIENT_STOCK = "INVENTORY_INSUFFICIENT_STOCK"

# ── Server ─────────────────────────────────────────────────────────────────────
SERVER_ERROR               = "SERVER_ERROR"
DB_ERROR                   = "DB_ERROR"

# ── Rate limit ─────────────────────────────────────────────────────────────────
RATE_LIMIT_EXCEEDED        = "RATE_LIMIT_EXCEEDED"