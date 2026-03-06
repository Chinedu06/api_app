import logging
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

logger = logging.getLogger("bookings")


def _send(subject: str, message: str, recipients: list[str]) -> None:
    """
    Safe email sender: never crashes booking flow.
    """
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
        logger.exception(f"[Email] Failed to send '{subject}' to {recipients}: {exc}")


def get_admin_emails() -> list[str]:
    """
    All staff + superuser admins should receive every booking alert.
    """
    User = get_user_model()
    qs = User.objects.filter(is_active=True).filter(is_staff=True) | User.objects.filter(is_active=True, is_superuser=True)
    return list(qs.values_list("email", flat=True))


def booking_summary_text(booking) -> str:
    """
    Plain text summary used in admin + tourist + operator emails.
    Uses snapshots so history is stable.
    """
    title = booking.service_title_snapshot or booking.service.title
    desc = booking.service_description_snapshot or ""
    inclusive = booking.service_inclusive_snapshot or ""
    duration = booking.service_duration_hours_snapshot

    duration_line = f"{duration} hour(s)" if duration else "N/A"

    return (
        f"Booking ID: {booking.pk}\n"
        f"Tour: {title}\n"
        f"Duration: {duration_line}\n"
        f"Start Date: {booking.start_date}\n"
        f"End Date: {booking.end_date or 'N/A'}\n"
        f"Adults: {booking.num_adults}\n"
        f"Children: {booking.num_children}\n"
        f"Customer: {booking.given_name} {booking.surname}\n"
        f"Email: {booking.email}\n"
        f"Phone: {booking.contact_number}\n"
        f"\n"
        f"Tour Description:\n{desc}\n"
        f"\n"
        f"Tour Inclusions:\n{inclusive}\n"
    )


def email_admin_new_booking(booking) -> None:
    subject = f"[New Booking] #{booking.pk} - {booking.service_title_snapshot or booking.service.title}"
    message = (
        "A new booking has been created on the platform.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
    )
    _send(subject, message, get_admin_emails())


def email_tourist_booking_received(booking) -> None:
    subject = f"Booking received (#{booking.pk})"
    message = (
        f"Hi {booking.given_name},\n\n"
        "Your booking request has been received successfully.\n"
        "You will receive another email once payment is confirmed and the operator confirms availability.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"Current Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        "\nThank you."
    )
    _send(subject, message, [booking.email])


def email_operator_booking_paid(booking) -> None:
    operator = getattr(booking.service, "operator", None)
    operator_email = getattr(operator, "email", None)

    subject = f"[Action Required] Paid booking #{booking.pk} - {booking.service_title_snapshot or booking.service.title}"
    message = (
        "A booking has been marked as PAID and is ready for your review.\n"
        "Please CONFIRM or REJECT based on your availability.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
    )
    _send(subject, message, [operator_email])


def email_tourist_booking_confirmed(booking) -> None:
    subject = f"Booking confirmed (#{booking.pk})"
    message = (
        f"Hi {booking.given_name},\n\n"
        "Good news — your booking has been CONFIRMED by the tour operator.\n\n"
        f"{booking_summary_text(booking)}\n"
        "\nThank you."
    )
    _send(subject, message, [booking.email])


def email_tourist_booking_rejected(booking) -> None:
    subject = f"Booking update (#{booking.pk})"
    reason = booking.admin_note or "No reason provided."
    message = (
        f"Hi {booking.given_name},\n\n"
        "Unfortunately, your booking was rejected by the operator.\n"
        f"Reason: {reason}\n\n"
        f"{booking_summary_text(booking)}\n"
        "\nThank you."
    )
    _send(subject, message, [booking.email])