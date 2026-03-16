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
    subject = "Welcome to the Allicom Tourism Partner Network!"
    message = (
        "Dear Operator,\n\n"
        "We are excited to have you join our Africa community of professional tour operators. "
        "By registering on our booking platform, you have taken a significant step toward expanding "
        "your reach and connecting with travelers seeking authentic, and  high-quality of Africa experiences.\n\n"
        "Your expertise is what makes our marketplace unique, and we look forward to showcasing your "
        "tour services to a wider audience.\n\n"
        "Next Steps to Get Started\n"
        "To begin managing your profile and uploading your tour packages, please log in to you account on our portal:\n\n"
        "Visit https://operators.allicomtourism.com/\n\n"
        "Use the username and password you created during the registration process.\n\n"
        "Once logged in, you will be able to update your company details, set your availability, and "
        "start listing your services for our travelers to discover.\n\n"
        "Note:\n"
        "If you encounter any issues accessing your account or have questions about setting up your listings, "
        "our professional support team is available 24/7 to assist you.\n\n"
        "Call/WhatsApp: +2348055853454\n"
        "E-mail: supports@allicomtourism.com\n\n"
        "We are excited to work together to promote wonders of Africa across the globe.\n\n"
        "Best regards,\n"
        "The Allicom Tourism Team"
    )
    _send(subject, message, [user.email])