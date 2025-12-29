from django.core.management.base import BaseCommand
from payments.models import Transaction


class Command(BaseCommand):
    help = "Reconcile Flutterwave payments"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting payment reconciliation..."))

        transactions = Transaction.objects.filter(
            provider="flutterwave",
            status="pending"
        )

        self.stdout.write(
            self.style.NOTICE(f"Found {transactions.count()} Flutterwave transactions to verify")
        )

        for tx in transactions:
            tx.sync_payment_from_transaction()

        self.stdout.write(self.style.SUCCESS("Payment reconciliation completed"))
