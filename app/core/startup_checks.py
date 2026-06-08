# 📁 app/core/startup_checks.py

from app.core.config import settings
from app.core.logger import logger


def run_startup_checks() -> None:
    """Run critical security checks before app starts."""
    errors = []
    warnings = []

    # ── SECRET_KEY strength ────────────────────────────────────────────────────
    if len(settings.SECRET_KEY) < settings.SECRET_KEY_MIN_LENGTH:
        errors.append(
            f"SECRET_KEY is too short ({len(settings.SECRET_KEY)} chars). "
            f"Minimum {settings.SECRET_KEY_MIN_LENGTH} required. "
            f"Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # ── DEBUG mode in production ───────────────────────────────────────────────
    if settings.ENVIRONMENT == "production" and settings.DEBUG:
        errors.append("DEBUG=True is NOT allowed in production environment!")

    # ── Weak default SECRET_KEY ────────────────────────────────────────────────
    weak_keys = {
        "your-super-secret-key-change-this-in-production",
        "secret",
        "changeme",
        "password",
    }
    if settings.SECRET_KEY.lower() in weak_keys:
        errors.append("SECRET_KEY is a known weak/default value. Please change it!")

    # ── CORS warning ───────────────────────────────────────────────────────────
    if settings.ENVIRONMENT == "production":
        warnings.append(
            "Remember to set CORS allow_origins to your domain in production!"
        )

    # ── Print warnings ─────────────────────────────────────────────────────────
    for warning in warnings:
        logger.warning(f"⚠️  Security warning : {warning}")

    # ── Raise on errors ────────────────────────────────────────────────────────
    if errors:
        for error in errors:
            logger.error(f"❌ Security check failed : {error}")
        raise RuntimeError(
            f"Security checks failed ({len(errors)} error(s)). "
            "Fix the above issues before starting the app."
        )

    logger.info("🔒 Security checks : ✅ passed")