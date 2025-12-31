import uuid
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from bookings.models import Booking
from payments.models import Transaction


@require_POST
@login_required
def initiate_bank_transfer(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    if booking.payment_status == "paid":
        return JsonResponse({"error": "Booking already paid"}, status=400)

    txn = Transaction.objects.create(
        booking=booking,
        amount=booking.service.price,
        provider=Transaction.PROVIDER_BANK,
        status=Transaction.STATUS_PENDING,
        reference=f"BANK-{uuid.uuid4().hex[:10].upper()}",
    )

    return JsonResponse({
        "message": "Bank transfer initiated",
        "reference": txn.reference,
        "bank_details": {
            "bank": settings.BANK_NAME,
            "account_name": settings.BANK_ACCOUNT_NAME,
            "account_number": settings.BANK_ACCOUNT_NUMBER,
        }
    })


@require_POST
@login_required
def upload_bank_receipt(request, reference):
    txn = Transaction.objects.get(reference=reference)

    if txn.provider != Transaction.PROVIDER_BANK:
        return JsonResponse({"error": "Invalid transaction"}, status=400)

    if txn.status != Transaction.STATUS_PENDING:
        return JsonResponse({"error": "Transaction not pending"}, status=400)

    receipt = request.FILES.get("receipt")
    if not receipt:
        return JsonResponse({"error": "Receipt required"}, status=400)

    txn.receipt = receipt
    txn.save(update_fields=["receipt", "updated_at"])

    return JsonResponse({"message": "Receipt uploaded. Awaiting admin approval"})


@require_POST
@staff_member_required
def approve_bank_transfer(request, reference):
    txn = Transaction.objects.get(reference=reference)

    if txn.provider != Transaction.PROVIDER_BANK:
        return JsonResponse({"error": "Not a bank transfer"}, status=400)

    if txn.status != Transaction.STATUS_PENDING:
        return JsonResponse({"error": "Already processed"}, status=400)

    if not txn.receipt:
        return JsonResponse({"error": "Receipt missing"}, status=400)

    txn.mark_successful()

    return JsonResponse({"message": "Bank transfer approved"})


@require_POST
@staff_member_required
def reject_bank_transfer(request, reference):
    txn = Transaction.objects.get(reference=reference)
    txn.mark_failed("Admin rejected transfer")

    return JsonResponse({"message": "Bank transfer rejected"})
