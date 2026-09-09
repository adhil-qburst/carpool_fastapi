import dramatiq

from app.core.email import send_verification_email
from app.tasks.broker import broker


@dramatiq.actor(queue_name="email")
def send_verification_email_task(
    to_email: str,
    token: str,
) -> None:
    send_verification_email(to_email, token)
