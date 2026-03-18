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


def email_operator_approved(user) -> None:
    subject = "Welcome to Allicom Tourism – Your Gateway to Global Visibility"
    message = (
        "Dear Partner,\n\n"
        "Welcome to Allicom Tourism, the largest African tourism platform for operators to integrate their products and services. "
        "We are excited to have you join our growing network of tour operators, car hire companies, recreation ventures, and hotel property owners.\n\n"
        "Our mission is to bridge the gap between high-quality service providers and a global audience. "
        "By partnering with us, you are now positioned to reach thousands of travel agents and potential customers internationally. "
        "We are committed to helping you increase your sales, expand your visibility, and achieve remarkable success together.\n\n"
        "General Policy Agreement\n\n"
        "1. Commission and Service Fees\n"
        "To maintain the operational integrity of the booking portal and provide continued marketing support, the following commission structure applies:\n\n"
        "Standard Rate: A minimum commission of 10% is required for all services listed on the platform.\n\n"
        "Negotiated Rates: In specific circumstances, a different commission percentage may be applied, provided it is mutually agreed upon in writing prior to the service listing.\n\n"
        "Pricing: All listed prices must be inclusive of the agreed-upon commission to ensure price consistency for the end traveler.\n\n"
        "2. Booking and Payment Settlement\n"
        "To protect the interests of both the traveler and the service provider, the settlement of funds for successful bookings will follow these protocols:\n\n"
        "Disbursement Timing: Payment for booked services will be processed either upon the commencement of the service or after the service has been rendered, as the case may be.\n\n"
        "Verification: Settlement is subject to the confirmation that the service was provided as described and that no significant disputes were raised during fulfillment.\n\n"
        "3. Operator Responsibilities\n"
        "Accuracy: Partners are responsible for ensuring that all descriptions, pricing, and availability calendars provided for the portal are accurate and updated in real-time.\n\n"
        "Service Standards: Partners must maintain the highest standards of professional conduct, safety, and reliability.\n\n"
        "4. Cancellation and Refunds\n"
        "All partners must adhere to a clear cancellation policy. In the event of a cancellation initiated by the operator, Allicom Tourism reserves the right to facilitate a full refund to the traveler to maintain platform trust.\n\n"
        "Next Steps\n\n"
        "By proceeding with your registration and listing your services on the Allicom Tourism booking portal, you acknowledge and agree to abide by the terms outlined above.\n\n"
        "We are excited to begin this journey with you and look forward to a robust partnership that promotes authentic experiences and drives excellence across the continent. "
        "Should you have any questions regarding these terms, please contact our operations department.\n\n"
        "Best regards,\n\n"
        "The Allicom Tourism Team\n"
        "Together, we can achieve remarkable success and sweeter sales!\n"
        f"{footer_text()}"
    )
    _send(subject, message, [user.email])