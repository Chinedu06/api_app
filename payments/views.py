import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.urls import reverse

from bookings.models import Booking
from .models import Transaction
from .services import verify_flutterwave_transaction

logger = logging.getLogger("payments")


# =====================================================================
# 1) Initialize Payment (Flutterwave)
# =====================================================================
def initialize_payment(request, booking_id):
    """
    1. User clicks "Pay Now"
    2. We create a Transaction
    3. Redirect user to Flutterwave checkout
    """

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return HttpResponseBadRequest("Invalid booking ID")

    # Amount must come from booking/service/package (not user)
    amount = Decimal(booking.service.price)

    # Create transaction
    reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    txn = Transaction.objects.create(
        booking=booking,
        reference=reference,
        amount=amount,
        provider=Transaction.PROVIDER_FLUTTERWAVE,
        status=Transaction.STATUS_INIT,
    )

    logger.info(f"[Init Payment] Created Txn {reference} for Booking {booking.id}")

    # Flutterwave redirect
    redirect_url = settings.FLUTTERWAVE_REDIRECT_URL.format(reference=reference)

    return JsonResponse({
        "payment_url": redirect_url,
        "reference": reference,
        "status": "ok"
    })


# =====================================================================
# 2) Flutterwave Redirect Success Handler
# =====================================================================
def payment_success(request):
    """
    2. User returns from Flutterwave after paying.
    Example callback: /payments/success?status=successful&tx_ref=TXN-123
    """

    reference = request.GET.get("tx_ref") or request.GET.get("reference")

    if not reference:
        return HttpResponseBadRequest("Missing tx_ref")

    try:
        txn = Transaction.objects.get(reference=reference)
    except Transaction.DoesNotExist:
        return HttpResponseBadRequest("Unknown transaction")

    verify_flutterwave_transaction(txn)

    # After verification, redirect to frontend success page
    frontend_url = settings.PAYMENT_FRONTEND_SUCCESS_URL.format(reference=reference)

    return redirect(frontend_url)


# =====================================================================
# 3) Flutterwave Redirect Failure Handler
# =====================================================================
def payment_cancelled(request):
    """
    Called when user cancels payment or fails at checkout.
    """
    reference = request.GET.get("tx_ref") or "(unknown)"

    logger.warning(f"[Payment Cancelled] User cancelled payment for {reference}")

    frontend_url = settings.PAYMENT_FRONTEND_CANCELLED_URL

    return redirect(frontend_url)


# =====================================================================
# 4) Flutterwave Webhook (MOST IMPORTANT)
# =====================================================================
@csrf_exempt
def flutterwave_webhook(request):
    """
    4. Flutterwave webhook verification (server → server)
    This is REQUIRED for real payments.
    """

    if request.method != "POST":
        return HttpResponse("Invalid method", status=405)

    try:
        payload = request.body.decode("utf-8")
        import json
        data = json.loads(payload)
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    logger.info(f"[FW Webhook] Received: {data}")

    reference = data.get("data", {}).get("tx_ref")

    if not reference:
        return HttpResponseBadRequest("Missing tx_ref")

    try:
        txn = Transaction.objects.get(reference=reference)
    except Transaction.DoesNotExist:
        return HttpResponseBadRequest("Unknown reference")

    # Save raw webhook metadata
    txn.meta = {
        **(txn.meta or {}),
        "webhook": data,
    }
    txn.save(update_fields=["meta"])

    # If payment is successful, verify with API
    if data.get("data", {}).get("status") == "successful":
        verify_flutterwave_transaction(txn)

    return HttpResponse("Webhook OK", status=200)


# =====================================================================
# 5) Debug Endpoint — Check Payment Status (optional)
# =====================================================================
def check_payment_status(request, reference):
    """
    Small optional endpoint used by frontend or mobile apps.
    """
    try:
        txn = Transaction.objects.get(reference=reference)
        booking = txn.booking
    except Transaction.DoesNotExist:
        return JsonResponse({"error": "Invalid reference"}, status=404)

    return JsonResponse({
        "reference": txn.reference,
        "status": txn.status,
        "provider": txn.provider,
        "amount": float(txn.amount),
        "booking_status": booking.status,
        "payment_status": booking.payment_status,
    })
