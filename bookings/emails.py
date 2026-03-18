import base64
import logging
from io import BytesIO
from pathlib import Path

import qrcode
from PIL import Image

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.contrib.auth import get_user_model

logger = logging.getLogger("bookings")


def get_booking_verify_url(booking) -> str:
    base_url = getattr(
        settings,
        "BOOKING_VERIFY_BASE_URL",
        "https://api.allicomtourism.com/api/v1/bookings/verify/",
    )
    return f"{base_url}{booking.booking_qr_token}/"


def get_qr_logo_path() -> Path:
    """
    Expected logo location inside the project.
    Put the uploaded logo file here on the server:

    <BASE_DIR>/assets/allicom-tourism-logo.png
    """
    return Path(settings.BASE_DIR) / "assets" / "allicom-tourism-logo.png"


def build_qr_code_base64(data: str) -> str | None:
    """
    Generates a QR code with logo and returns base64 PNG string
    for inline HTML email display.
    """
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        logo_path = get_qr_logo_path()
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")

            qr_width, qr_height = image.size
            logo_size = qr_width // 4
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            image.paste(logo, pos, logo)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode("utf-8")
    except Exception as exc:
        logger.exception(f"[QR] Failed to generate QR code: {exc}")
        return None


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
        logger.exception(f"[Email] Failed to send '{subject}' to {recipients}: {exc}")


def _send_html(subject: str, text_body: str, html_body: str, recipients: list[str]) -> None:
    recipients = [r for r in recipients if r]
    if not recipients:
        return

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=recipients,
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
    except Exception as exc:
        logger.exception(f"[HTML Email] Failed to send '{subject}' to {recipients}: {exc}")


def get_admin_emails() -> list[str]:
    User = get_user_model()
    qs = User.objects.filter(is_active=True, is_staff=True) | User.objects.filter(
        is_active=True,
        is_superuser=True,
    )
    qs = qs.distinct()
    return [email for email in qs.values_list("email", flat=True) if email]


def format_money(value) -> str:
    if value is None:
        return "N/A"
    return f"{value}"


def booking_summary_text(booking) -> str:
    title = booking.service_title_snapshot or booking.service.title
    desc = booking.service_description_snapshot or ""
    inclusive = booking.service_inclusive_snapshot or ""
    duration = booking.service_duration_hours_snapshot
    package_name = booking.package.name if booking.package else "N/A"

    duration_line = f"{duration} hour(s)" if duration else "N/A"

    return (
        f"Booking ID: {booking.pk}\n"
        f"Tour: {title}\n"
        f"Package: {package_name}\n"
        f"Duration: {duration_line}\n"
        f"Service Price Snapshot: {format_money(booking.service_price_snapshot)}\n"
        f"Package Price Snapshot: {format_money(booking.package_price_snapshot)}\n"
        f"Final Booked Price: {format_money(booking.final_price_snapshot)}\n"
        f"Start Date: {booking.start_date}\n"
        f"End Date: {booking.end_date or 'N/A'}\n"
        f"Adults: {booking.num_adults}\n"
        f"Children: {booking.num_children}\n"
        f"Customer: {booking.given_name} {booking.surname}\n"
        f"Email: {booking.email}\n"
        f"Phone: {booking.contact_number}\n"
        f"Nationality: {getattr(booking, 'nationality', '') or 'N/A'}\n"
        f"Current Residence: {getattr(booking, 'current_residence', '') or 'N/A'}\n"
        f"ID Card Type: {booking.get_id_card_type_display() if getattr(booking, 'id_card_type', '') else 'N/A'}\n"
        f"\n"
        f"Tour Description:\n{desc}\n"
        f"\n"
        f"Tour Inclusions:\n{inclusive}\n"
    )


def payment_summary_text(booking) -> str:
    payment = getattr(booking, "payment", None)
    provider = getattr(payment, "provider", None) or "N/A"
    reference = getattr(payment, "reference", None) or "N/A"
    amount = getattr(payment, "amount", None) or booking.booked_total_price
    paid_at = getattr(payment, "paid_at", None) or "N/A"

    return (
        f"Payment Provider: {provider}\n"
        f"Payment Reference: {reference}\n"
        f"Payment Amount: {format_money(amount)}\n"
        f"Paid At: {paid_at}\n"
    )


def footer_text() -> str:
    return (
        "\n"
        "Sincerely,\n"
        "Allicom Tourism (Allicom Consultancy Limited)\n"
        "| Tour Booking | Tour Packages | Hotels | Cars hire | Visa Support | Insurance |\n\n"
        "Office Addresses:\n\n"
        "NG: 92, Lewis Street, off Okesuna Street, Lagos Island, Lagos, Nigeria.\n"
        "Landmark: Obalende/High Court\n\n"
        "UK: Unit C Aldow Enterprise Park, Blackett Street, Manchester, United Kingdom.\n\n"
        "Mobile: (+234) 08067663986, 08071729330\n"
        "Website: https://allicomtravels.com\n"
    )


def footer_html() -> str:
    return """
    <hr style="margin-top: 30px; margin-bottom: 20px; border: none; border-top: 1px solid #ddd;" />

    <p><strong>Sincerely,</strong><br />
    Allicom Tourism (Allicom Consultancy Limited)</p>

    <p>
        <a href="https://allicomtravels.com/services/" target="_blank">Tour Booking</a> |
        <a href="https://tourism.allicomtravels.com" target="_blank">Tour Packages</a> |
        <a href="https://allicomtravels.com/services/" target="_blank">Hotels</a> |
        <a href="https://www.allicomtravels.com" target="_blank">Cars hire</a> |
        <a href="https://allicomtravels.com/services/" target="_blank">Visa Support</a> |
        <a href="https://www.allicomtravels.com" target="_blank">Insurance</a>
    </p>

    <p><strong>Office Addresses:</strong></p>

    <p>
        <strong>NG:</strong> 92, Lewis Street, off Okesuna Street, Lagos Island, Lagos, Nigeria.<br />
        Landmark: Obalende/High Court
    </p>

    <p>
        <strong>UK:</strong> Unit C Aldow Enterprise Park, Blackett Street, Manchester, United Kingdom.
    </p>

    <p>
        <strong>Mobile:</strong>
        <a href="tel:+2348067663986">(+234) 08067663986</a>,
        <a href="tel:+2348071729330">08071729330</a>
    </p>

    <p>
        <strong>Website:</strong>
        <a href="https://allicomtravels.com" target="_blank">Allicomtourism</a>
    </p>
    """


def email_admin_new_booking(booking) -> None:
    subject = f"[New Booking] #{booking.pk} - {booking.service_title_snapshot or booking.service.title}"
    message = (
        "A new booking has been created on the platform.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"{footer_text()}"
    )
    _send(subject, message, get_admin_emails())


def email_admin_payment_received(booking) -> None:
    subject = f"[Payment Received] Booking #{booking.pk} - {booking.service_title_snapshot or booking.service.title}"
    message = (
        "Payment has been received successfully for the booking below.\n"
        "The booking is now pending operator confirmation.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{payment_summary_text(booking)}\n"
        f"Booking Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"{footer_text()}"
    )
    _send(subject, message, get_admin_emails())


def email_admin_booking_confirmed(booking) -> None:
    subject = f"[Booking Confirmed] #{booking.pk} - {booking.service_title_snapshot or booking.service.title}"
    message = (
        "The operator has confirmed the booking below.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{payment_summary_text(booking)}\n"
        f"Booking Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"{footer_text()}"
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
        f"{footer_text()}"
    )
    _send(subject, message, [booking.email])


def email_tourist_payment_received(booking) -> None:
    subject = f"Payment received successfully (#{booking.pk})"
    message = (
        f"Hi {booking.given_name},\n\n"
        "Your payment for this booking has been received successfully.\n"
        "Your booking is now pending confirmation by the tour operator.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{payment_summary_text(booking)}\n"
        f"Current Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"{footer_text()}"
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
        f"{payment_summary_text(booking)}\n"
        f"Status: {booking.status}\n"
        f"Payment Status: {booking.payment_status}\n"
        f"{footer_text()}"
    )
    _send(subject, message, [operator_email])


def email_tourist_booking_confirmed(booking) -> None:
    subject = f"Booking confirmed (#{booking.pk})"
    verify_url = get_booking_verify_url(booking)
    qr_base64 = build_qr_code_base64(verify_url)

    text_message = (
        f"Hi {booking.given_name},\n\n"
        "Good news — your booking has been CONFIRMED by the tour operator.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{payment_summary_text(booking)}\n"
        f"Booking Verification Link:\n{verify_url}\n\n"
        "Please keep this email safe and present the QR code or verification link at check-in.\n"
        f"{footer_text()}"
    )

    qr_html = (
        f'<p><img src="data:image/png;base64,{qr_base64}" alt="Booking QR Code" style="max-width:260px;height:auto;" /></p>'
        if qr_base64
        else ""
    )

    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #222;">
            <p>Hi {booking.given_name},</p>

            <p><strong>Good news — your booking has been CONFIRMED by the tour operator.</strong></p>

            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{booking_summary_text(booking)}</pre>
            <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{payment_summary_text(booking)}</pre>

            <p><strong>Booking Verification Link:</strong><br />
            <a href="{verify_url}">{verify_url}</a></p>

            <p><strong>Booking QR Code:</strong></p>
            {qr_html}

            <p>Please keep this email safe and present the QR code or verification link at check-in.</p>

            {footer_html()}
        </body>
    </html>
    """

    _send_html(subject, text_message, html_message, [booking.email])


def email_tourist_booking_rejected(booking) -> None:
    subject = f"Booking update (#{booking.pk})"
    reason = booking.admin_note or "No reason provided."
    message = (
        f"Hi {booking.given_name},\n\n"
        "Unfortunately, your booking was rejected by the operator.\n"
        f"Reason: {reason}\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{footer_text()}"
    )
    _send(subject, message, [booking.email])