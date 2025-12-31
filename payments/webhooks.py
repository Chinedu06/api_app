import json
import hmac
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import extend_schema

from .models import Transaction
from .services import verify_flutterwave_transaction

logger = logging.getLogger("payments")


# ==========================================================
# Signature Verification (SECURITY CRITICAL)
# ==========================================================
def verify_flutterwave_signature(request):
    """
    Flutterwave sends `verif-hash` header.
    We must compare it against our secret hash.
    """
    received_hash = request.headers.get("verif-hash")

    if not received_hash:
        logger.warning("[FW Webhook] Missing verif-hash header")
        return False

    secret_hash = settings.FLUTTERWAVE_SECRET_HASH

    if not secret_hash:
        logger.error("[FW Webhook] FLUTTERWAVE_SECRET_HASH not set")
        return False

    return hmac.compare_digest(received_hash, secret_hash)


# ==========================================================
# Flutterwave Webhook Handler
# ==========================================================
@csrf_exempt
@extend_schema(exclude=True)  # 🔒 HIDE FROM SWAGGER / REDOC
def flutterwave_webhook(request):
    """
    Flutterwave server-to-server webhook.
    This endpoint MUST:
    - Validate signature
    - Be idempotent
    - Never trust frontend redirects
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    # ------------------------------------------------------
    # 1️⃣ Verify webhook signature
    # ------------------------------------------------------
    if not verify_flutterwave_signature(request):
        return HttpResponseForbidden("Invalid webhook signature")

    # ------------------------------------------------------
    # 2️⃣ Parse payload
    # ------------------------------------------------------
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        logger.exception("[FW Webhook] Invalid JSON payload")
        return HttpResponseBadRequest("Invalid JSON")

    logger.info(f"[FW Webhook] Payload received: {payload}")

    event = payload.get("event")
    data = payload.get("data", {})

    # We only care about completed charges
    if event != "charge.completed":
        return HttpResponse("Ignored", status=200)

    reference = data.get("tx_ref")

    if not reference:
        logger.warning("[FW Webhook] Missing tx_ref")
        return HttpResponseBadRequest("Missing tx_ref")

    # ------------------------------------------------------
    # 3️⃣ Locate transaction
    # ------------------------------------------------------
    try:
        txn = Transaction.objects.get(reference=reference)
    except Transaction.DoesNotExist:
        logger.error(f"[FW Webhook] Unknown transaction reference: {reference}")
        return HttpResponseBadRequest("Unknown transaction")

    # ------------------------------------------------------
    # 4️⃣ Store raw webhook payload (for audit)
    # ------------------------------------------------------
    txn.meta = {
        **(txn.meta or {}),
        "flutterwave_webhook": payload,
    }
    txn.save(update_fields=["meta", "updated_at"])

    # ------------------------------------------------------
    # 5️⃣ Idempotency check
    # ------------------------------------------------------
    if txn.status == Transaction.STATUS_SUCCESS:
        logger.info(f"[FW Webhook] Transaction already processed: {reference}")
        return HttpResponse("Already processed", status=200)

    # ------------------------------------------------------
    # 6️⃣ Server-side verification (SOURCE OF TRUTH)
    # ------------------------------------------------------
    try:
        verify_flutterwave_transaction(txn)
    except Exception:
        logger.exception(f"[FW Webhook] Verification failed for {reference}")
        return HttpResponse("Verification error", status=500)

    return HttpResponse("Webhook processed", status=200)
