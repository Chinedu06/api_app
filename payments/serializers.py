from rest_framework import serializers
from .models import Transaction, Payment
from bookings.models import Booking


# ---------------------------------------------------------
# PAYMENT INITIATION SERIALIZER
# ---------------------------------------------------------
class PaymentInitiateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    provider = serializers.ChoiceField(
        choices=[
            ("flutterwave", "Flutterwave"),
            ("interswitch", "Interswitch"),
            ("bank_transfer", "Bank Transfer"),
        ]
    )

    def validate_booking_id(self, value):
        if not Booking.objects.filter(id=value).exists():
            raise serializers.ValidationError("Booking does not exist.")
        return value


# ---------------------------------------------------------
# TRANSACTION SERIALIZER
# ---------------------------------------------------------
class TransactionSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "booking",
            "provider",
            "amount",
            "status",
            "flutterwave_id",
            "created_at",
            "updated_at",
            "meta",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


# ---------------------------------------------------------
# PAYMENT SERIALIZER
# ---------------------------------------------------------
class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "reference",
            "amount",
            "provider",
            "status",
            "paid_at",
        ]
        read_only_fields = [
            "booking",
            "paid_at",
            "status",
        ]
