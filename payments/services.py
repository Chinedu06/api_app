import logging
import requests
from django.conf import settings
from django.utils import timezone

from .models import Transaction

logger = logging.getLogger("payments")


# ---------------------------------------------------------
# FLUTTERWAVE VERIFY CALL (USED BY WEBHOOK + RETRY)
# ---------------------------------------------------------
def verify_flutterwave_transaction(txn: Transaction):
    """
    Calls Flutterwave's v3 verify API for a given Transaction.
    Returns the parsed API data or None on failure.
    """

    if not txn.flutterwave_id:
        logger.warning(f"[FW VERIFY] No flutterwave_id for txn {txn.reference}")
        return None

    url = f"https://api.flutterwave.com/v3/transactions/{txn.flutterwave_id}/verify"

    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    logger.info(f"[FW VERIFY] Verifying FW transaction {txn.flutterwave_id}")

    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
    except Exception as e:
        logger.exception(f"[FW VERIFY] Network error: {e}")
        return None

    # Save raw data for audit
    txn.meta = {
        **(txn.meta or {}),
        "last_fw_verify": data,
        "last_verify_time": str(timezone.now()),
    }
    txn.save(update_fields=["meta"])

    return data


# ---------------------------------------------------------
# RETRY GATEWAY VERIFICATION (ADMIN ACTION)
# ---------------------------------------------------------
def retry_gateway_verification(txn: Transaction):
    """
    Unified verification entrypoint.
    Works for Flutterwave and can be extended for more gateways.
    Returns a simple result string.
    """

    if txn.provider != Transaction.PROVIDER_FLUTTERWAVE:
        return "IGNORED — only Flutterwave supported for retry right now."

    data = verify_flutterwave_transaction(txn)

    if not data:
        return "FAILED — could not verify transaction"

    fw_status = data.get("data", {}).get("status")

    if fw_status == "successful":
        txn.mark_successful()
        return "SUCCESS — transaction marked successful"

    elif fw_status in ["failed", "cancelled"]:
        txn.mark_failed("Gateway returned failed/cancelled")
        return "FAILED — gateway returned failed/cancelled"

    else:
        return f"PENDING — gateway status = {fw_status}"
