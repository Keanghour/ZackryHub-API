# 📁 app/core/email.py

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings
from app.core.logger import logger

# ── Mail connection config ─────────────────────────────────────────────────────
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)

fastmail = FastMail(mail_config)


# ── Send password reset email ──────────────────────────────────────────────────
async def send_reset_password_email(email: str, name: str, token: str) -> None:
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p>Hi <strong>{name}</strong>,</p>
        <p>We received a request to reset your password. Click the button below to reset it:</p>
        <a href="{reset_link}"
           style="display: inline-block; padding: 12px 24px; background-color: #4F46E5;
                  color: white; text-decoration: none; border-radius: 6px; margin: 16px 0;">
            Reset Password
        </a>
        <p>Or copy this link into your browser:</p>
        <p style="color: #666; word-break: break-all;">{reset_link}</p>
        <p><strong>This link will expire in 15 minutes.</strong></p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px;">
            If you did not request a password reset, please ignore this email.
        </p>
    </div>
    """

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=html_body,
        subtype=MessageType.html,
    )

    try:
        await fastmail.send_message(message)
        logger.info(f"Reset email sent | email={email}")
    except Exception as e:
        logger.error(f"Failed to send reset email | email={email} | error={e}")
        raise