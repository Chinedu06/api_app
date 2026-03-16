import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("users")


def _send(subject: str, message: str, recipients: list[str]) -> None:
    recipients = [r for r in recipients if r]
    if not recipients:
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception(f"[User Email] Failed to send '{subject}' to {recipients}: {exc}")


def email_operator_approved(user) -> None:
    subject = "Your operator account has been approved"
    message = (
        f"Hello {user.username},\n\n"
        "Your operator account has been approved successfully by the admin.\n"
        "You can now log in and start managing your tours on the platform.\n\n"
        "Thank you."
    )
    _send(subject, message, [user.email])