import logging
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

logger = logging.getLogger("bookings")


def _safe_send_mail(subject: str, message: str, recipients: list[str]) -> None:
    """
    Sends email safely (never crashes your API if email is not configured yet).
    """
    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "no-reply@api.allicomtourism.com"
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception as e:
        logger.exception(f"Email send failed to {recipients}: {e}")


def get_admin_emails() -> list[str]:
    """
    All staff + superusers should receive booking emails.
    """
    User = get_user_model()
    qs = User.objects.filter(is_active=True).filter(is_staff=True) | User.objects.filter(is_active=True).filter(is_superuser=True)
    qs = qs.distinct()
    return [u.email for u in qs if u.email]


def email_admins_new_booking(booking) -> None:
    subject = f"New booking #{booking.pk} received"
    message = (
        f"A new booking has been created.\n\n"
        f"Booking ID: {booking.pk}\n"
        f"Service: {booking.service_title_snapshot or booking.service.title}\n"
        f"Tourist: {booking.given_name} {booking.surname}\n"
        f"Email: {booking.email}\n"
        f"Phone: {booking.contact_number}\n"
        f"Adults: {booking.num_adults} | Children: {booking.num_children}\n"
        f"Dates: {booking.start_date} → {booking.end_date}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"Booking Status: {booking.status}\n"
    )
    _safe_send_mail(subject, message, get_admin_emails())


def email_tourist_booking_received(booking) -> None:
    subject = f"Booking received (#{booking.pk})"
    duration = booking.service_duration_hours_snapshot
    duration_text = f"{duration} hour(s)" if duration else "N/A"

    message = (
        f"Hi {booking.given_name},\n\n"
        f"Your booking request was received successfully.\n\n"
        f"Booking ID: {booking.pk}\n"
        f"Tour: {booking.service_title_snapshot or booking.service.title}\n"
        f"Duration: {duration_text}\n"
        f"Dates: {booking.start_date} → {booking.end_date}\n"
        f"Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n\n"
        f"Tour Description:\n{booking.service_description_snapshot or ''}\n\n"
        f"Inclusions:\n{booking.service_inclusive_snapshot or ''}\n\n"
        f"Thank you."
    )
    _safe_send_mail(subject, message, [booking.email])


def email_operator_booking_paid(booking) -> None:
    """
    Payment has been confirmed (gateway success OR bank approved).
    Operator can now confirm/reject booking.
    """
    operator = getattr(booking.service, "operator", None)
    if not operator or not operator.email:
        return

    subject = f"Booking #{booking.pk} is PAID — action required"
    message = (
        f"Hello {getattr(operator, 'username', 'Operator')},\n\n"
        f"Booking #{booking.pk} for your tour is now marked as PAID.\n"
        f"You can now confirm or reject it.\n\n"
        f"Tour: {booking.service_title_snapshot or booking.service.title}\n"
        f"Tourist: {booking.given_name} {booking.surname} ({booking.email})\n"
        f"Dates: {booking.start_date} → {booking.end_date}\n"
    )
    _safe_send_mail(subject, message, [operator.email])


def email_tourist_booking_confirmed(booking) -> None:
    subject = f"Booking confirmed (#{booking.pk})"
    duration = booking.service_duration_hours_snapshot
    duration_text = f"{duration} hour(s)" if duration else "N/A"

    message = (
        f"Hi {booking.given_name},\n\n"
        f"Your booking has been CONFIRMED by the tour operator.\n\n"
        f"Booking ID: {booking.pk}\n"
        f"Tour: {booking.service_title_snapshot or booking.service.title}\n"
        f"Duration: {duration_text}\n"
        f"Dates: {booking.start_date} → {booking.end_date}\n\n"
        f"Tour Description:\n{booking.service_description_snapshot or ''}\n\n"
        f"Inclusions:\n{booking.service_inclusive_snapshot or ''}\n\n"
        f"Thank you."
    )
    _safe_send_mail(subject, message, [booking.email])


def email_tourist_booking_rejected(booking) -> None:
    subject = f"Booking declined (#{booking.pk})"
    reason = booking.admin_note or "No reason provided."

    message = (
        f"Hi {booking.given_name},\n\n"
        f"Unfortunately your booking was declined by the tour operator.\n\n"
        f"Booking ID: {booking.pk}\n"
        f"Tour: {booking.service_title_snapshot or booking.service.title}\n"
        f"Reason: {reason}\n\n"
        f"Thank you."
    )
    _safe_send_mail(subject, message, [booking.email])