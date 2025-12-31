from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import Transaction
from payments.services import verify_flutterwave_transaction


class Command(BaseCommand):
    help = "Reconcile pending or failed payment transactions"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🔄 Starting payment reconciliation…"))

        # ---------------------------------------------
        # 1️⃣ Flutterwave Transactions (auto-verifiable)
        # ---------------------------------------------
        flutterwave_txns = Transaction.objects.filter(
            provider=Transaction.PROVIDER_FLUTTERWAVE,
            status__in=[Transaction.STATUS_INIT, Transaction.STATUS_PENDING],
        )

        self.stdout.write(
            f"🔍 Found {flutterwave_txns.count()} Flutterwave transactions to verify"
        )

        for txn in flutterwave_txns:
            try:
                self.stdout.write(f"→ Verifying {txn.reference}")
                verify_flutterwave_transaction(txn)
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(
                        f"❌ Error verifying {txn.reference}: {exc}"
                    )
                )

        # ---------------------------------------------
        # 2️⃣ Bank Transfers (manual — report only)
        # ---------------------------------------------
        bank_txns = Transaction.objects.filter(
            provider=Transaction.PROVIDER_BANK,
            status=Transaction.STATUS_PENDING,
        )

        if bank_txns.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"🏦 {bank_txns.count()} bank transfer(s) pending manual approval"
                )
            )
            for txn in bank_txns:
                self.stdout.write(
                    f"   - {txn.reference} | Booking #{txn.booking_id} | ₦{txn.amount}"
                )

        # ---------------------------------------------
        # DONE
        # ---------------------------------------------
        self.stdout.write(self.style.SUCCESS("✅ Payment reconciliation completed"))
