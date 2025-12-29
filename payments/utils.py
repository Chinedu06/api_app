# payments/utils.py
import json
import logging
from django.conf import settings

logger = logging.getLogger("payments")


# ----------------------------------------------------
# 1. Verify Flutterwave Webhook Signature
# ----------------------------------------------------

def verify_flutterwave_signature(request):
    """
    Validates Flutterwave's webhook signature using:
    Header: verif-hash
    Env var: FLW_SECRET_HASH

    Returns:
        True  -> signature valid
        False -> invalid
    """

    received_hash = request.headers.get("verif-hash")
    expected_hash = settings.FLW_SECRET_HASH

    logger.info(f"[SIGNATURE] Received={received_hash} | Expected={expected_hash}")

    if not received_hash:
        logger.warning("[SIGNATURE] Missing verif-hash header")
        return False

    if not expected_hash:
        logger.error("[SIGNATURE] FLW_SECRET_HASH not set in settings or .env")
        return False

    if received_hash.strip() != expected_hash.strip():
        logger.warning("[SIGNATURE] Invalid webhook signature")
        return False

    return True


# ----------------------------------------------------
# 2. Safe JSON extractor
# ----------------------------------------------------

def safe_json(request):
    """
    Safely extracts JSON from request.body without crashing views.
    """
    try:
        return json.loads(request.body.decode())
    except Exception:
        logger.warning("[UTILS] Failed to parse JSON body")
        return {}


# ----------------------------------------------------
# 3. Normalize tx_ref (some gateways send txRef or tx_ref)
# ----------------------------------------------------

def normalize_reference(ref):
    """
    Converts txRef / tx_ref / TX_REF / random formatting into clean reference.
    """
    if not ref:
        return None
    return str(ref).strip()

# ----------------------------------------------------
# 4. Safe Transaction Getter
# ----------------------------------------------------

def safe_get_txn(reference, TransactionModel=None):
    """
    Safely load a Transaction by reference.
    Used in views, webhook handlers, and verification.

    Args:
        reference (str): The transaction reference string.
        TransactionModel: Optional override for easier testing.

    Returns:
        Transaction instance | None
    """
    if not reference:
        logger.warning("[UTILS] safe_get_txn called with empty reference")
        return None

    try:
        from .models import Transaction  # lazy import prevents circular import errors
        Model = TransactionModel or Transaction
        return Model.objects.filter(reference=str(reference).strip()).first()

    except Exception as e:
        logger.error(f"[UTILS] Failed to load transaction {reference}: {e}")
        return None
