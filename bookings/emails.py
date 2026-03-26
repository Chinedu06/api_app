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
    """
    Frontend ticket URL used in email button + QR.
    Frontend page should extract the token and call backend verify API.
    """
    base_url = getattr(
        settings,
        "BOOKING_TICKET_FRONTEND_URL",
        "https://tourism.allicomtravels.com/ticket/",
    ).rstrip("/")
    return f"{base_url}/{booking.booking_qr_token}"


def get_backend_verify_api_url(booking) -> str:
    """
    Backend verification API URL.
    Kept for reference/debugging if needed.
    """
    base_url = getattr(
        settings,
        "BOOKING_VERIFY_BASE_URL",
        "https://api.allicomtourism.com/api/v1/bookings/verify/",
    ).rstrip("/")
    return f"{base_url}/{booking.booking_qr_token}/"


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
        <a href="https://allicomtravels.com/services/" target="_blank">Cars hire</a> |
        <a href="https://allicomtravels.com/services/" target="_blank">Visa Support</a> |
        <a href="https://allicomtravels.com/services/" target="_blank">Insurance</a>
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
    """
    Final confirmation email using the new HTML template.
    Placeholder variables are replaced with actual booking values.
    """
    subject = f"Booking confirmed (#{booking.pk})"

    verification_link = get_booking_verify_url(booking)
    qr_base64 = build_qr_code_base64(verification_link)
    qr_code_image_url = (
        f"data:image/png;base64,{qr_base64}" if qr_base64 else ""
    )

    customer_first_name = booking.given_name or ""
    customer_full_name = f"{booking.given_name} {booking.surname}".strip()
    tour_title = booking.service_title_snapshot or booking.service.title
    package_name = booking.package.name if booking.package else "N/A"
    duration = (
        f"{booking.service_duration_hours_snapshot} hour(s)"
        if booking.service_duration_hours_snapshot
        else "N/A"
    )
    start_date = str(booking.start_date) if booking.start_date else "N/A"
    end_date = str(booking.end_date) if booking.end_date else "N/A"
    final_price = format_money(booking.final_price_snapshot or booking.booked_total_price)
    payment_status = booking.payment_status.title() if booking.payment_status else "N/A"

    text_message = (
        f"Hi {customer_first_name},\n\n"
        "Good news — your booking has been CONFIRMED by the tour operator.\n\n"
        f"{booking_summary_text(booking)}\n"
        f"{payment_summary_text(booking)}\n"
        f"Online Ticket:\n{verification_link}\n\n"
        "Please keep this email safe and present the QR code or ticket page at check-in.\n"
        f"{footer_text()}"
    )

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Booking Confirmation - Allicom Tourism</title>
    <style>
        body { margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
        .wrapper { width: 100%; table-layout: fixed; background-color: #f8fafc; padding: 40px 0; }
        .main { background-color: #ffffff; margin: 0 auto; width: 100%; max-width: 600px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
        .header { background-color: #1e3a8a; padding: 30px; text-align: center; color: #ffffff; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }
        .header p { margin: 5px 0 0 0; font-size: 14px; color: #bfdbfe; }
        .content { padding: 40px 30px; color: #334155; }
        .success-banner { background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 15px 20px; border-radius: 4px; margin-bottom: 30px; }
        .success-banner h2 { margin: 0 0 5px 0; color: #065f46; font-size: 18px; }
        .success-banner p { margin: 0; color: #047857; font-size: 14px; line-height: 1.5; }
        .section-title { font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 15px; margin-top: 30px; }
        .grid { display: block; width: 100%; }
        .row { margin-bottom: 12px; font-size: 14px; line-height: 1.6; }
        .label { font-weight: 700; color: #475569; display: inline-block; width: 140px; }
        .value { color: #0f172a; }
        .price-box { background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin-top: 20px; text-align: right; }
        .price-box .total { font-size: 24px; font-weight: 800; color: #1e3a8a; margin-top: 5px; }
        .qr-section { text-align: center; margin-top: 40px; padding-top: 30px; border-top: 2px dashed #e2e8f0; }
        .qr-code { max-width: 200px; height: auto; margin: 20px auto; border: 10px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 8px; }
        .btn { display: inline-block; background-color: #2563eb; color: #ffffff !important; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: 600; font-size: 15px; margin-top: 15px; }
        .footer { text-align: center; padding: 30px; color: #64748b; font-size: 12px; line-height: 1.6; background-color: #f8fafc; }
        @media screen and (max-width: 600px) {
            .main { border-radius: 0; }
            .content { padding: 30px 20px; }
            .label { display: block; width: 100%; margin-bottom: 2px; color: #64748b; }
            .row { margin-bottom: 16px; }
        }
    </style>
</head>
<body>
    <main class="wrapper">
        <div class="main">
            <div class="header">
                <h1>Allicom Tourism</h1>
                <p>Explore Africa, Explore Cultures!</p>
            </div>

            <div class="content">
                <div class="success-banner">
                    <h2>Booking Confirmed!</h2>
                    <p>Hi {{ customer_first_name }}, good news! Your tour operator has successfully confirmed your booking.</p>
                </div>

                <div class="section-title">Tour Details</div>
                <div class="grid">
                    <div class="row"><span class="label">Booking ID:</span> <span class="value">#{{ booking_id }}</span></div>
                    <div class="row"><span class="label">Tour Name:</span> <span class="value"><strong>{{ tour_title }}</strong></span></div>
                    <div class="row"><span class="label">Package:</span> <span class="value" style="text-transform: capitalize;">{{ package_name }}</span></div>
                    <div class="row"><span class="label">Duration:</span> <span class="value">{{ duration }}</span></div>
                    <div class="row"><span class="label">Start Date:</span> <span class="value">{{ start_date }}</span></div>
                    <div class="row"><span class="label">End Date:</span> <span class="value">{{ end_date }}</span></div>
                    <div class="row"><span class="label">Guests:</span> <span class="value">{{ num_adults }} Adult(s), {{ num_children }} Child(ren)</span></div>
                </div>

                <div class="section-title">Customer Details</div>
                <div class="grid">
                    <div class="row"><span class="label">Name:</span> <span class="value">{{ customer_full_name }}</span></div>
                    <div class="row"><span class="label">Email:</span> <span class="value">{{ customer_email }}</span></div>
                    <div class="row"><span class="label">Phone:</span> <span class="value">{{ customer_phone }}</span></div>
                </div>

                <div class="price-box">
                    <div style="color: #64748b; font-size: 13px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Final Booked Price</div>
                    <div class="total">${{ final_price }}</div>
                    <div style="color: #10b981; font-weight: 600; font-size: 14px; margin-top: 8px;">
                        Payment Status: {{ payment_status }}
                    </div>
                </div>

                <div class="qr-section">
                    <h3 style="margin: 0; color: #0f172a; font-size: 18px;">Your Digital Ticket</h3>
                    <p style="margin: 8px 0 0 0; color: #64748b; font-size: 14px;">Please keep this email safe and present the QR code to your operator at check-in.</p>

                    <img src="{{ qr_code_image_url }}" alt="Booking QR Code" class="qr-code">

                    <div>
                        <a href="{{ verification_link }}" class="btn">View Online Ticket</a>
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>Need help? Contact our support team at <a href="mailto:supports@allicomtourism.com" style="color: #2563eb; text-decoration: none;">supports@allicomtourism.com</a></p>
                <p>&copy; 2026 Allicom Tourism. All Rights Reserved.</p>
            </div>
        </div>
    </main>
</body>
</html>"""

    replacements = {
        "{{ customer_first_name }}": customer_first_name,
        "{{ booking_id }}": str(booking.pk),
        "{{ tour_title }}": tour_title,
        "{{ package_name }}": package_name,
        "{{ duration }}": duration,
        "{{ start_date }}": start_date,
        "{{ end_date }}": end_date,
        "{{ num_adults }}": str(booking.num_adults),
        "{{ num_children }}": str(booking.num_children),
        "{{ customer_full_name }}": customer_full_name,
        "{{ customer_email }}": booking.email or "",
        "{{ customer_phone }}": booking.contact_number or "",
        "{{ final_price }}": final_price,
        "{{ payment_status }}": payment_status,
        "{{ qr_code_image_url }}": qr_code_image_url,
        "{{ verification_link }}": verification_link,
    }

    html_message = html_template
    for placeholder, value in replacements.items():
        html_message = html_message.replace(placeholder, value)

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