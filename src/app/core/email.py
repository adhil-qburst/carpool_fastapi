import logging
import smtplib
from email.message import EmailMessage

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def send_verification_email(
    to_email: str,
    token: str,
    *,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    verify_url = f"{settings.email_verification_base_url}?token={token}"

    message = EmailMessage()
    message["Subject"] = "Verify your CarPool account"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "Welcome to CarPool.\n\n"
        "Please verify your email by opening this link:\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.email_verification_expire_hours} hours.\n"
        "If you did not create this account, you can ignore this email.\n"
    )

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=30,
    ) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)

    logger.info("Sent verification email to %s", to_email)
