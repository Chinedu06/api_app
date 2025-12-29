from rest_framework import serializers
from .models import Booking, Notification
from services.models import Package, Service


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing bookings.
    Includes full personal details + package + service.
    """

    service_title = serializers.CharField(source="service.title", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "service",
            "service_title",
            "package",
            "package_name",

            # Personal details
            "given_name",
            "surname",
            "other_names",
            "contact_number",
            "email",
            "full_contact_address",

            # Travelers
            "num_adults",
            "num_children",

            # Trip dates
            "start_date",
            "end_date",

            # Notes
            "notes",
            "admin_note",

            # Status + Payment
            "status",
            "payment_status",

            # Timestamps
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "status",
            "payment_status",
            "created_at",
            "updated_at",
            "admin_note",
            "user",
        )

    # ============================================
    # VALIDATION
    # ============================================

    def validate(self, attrs):
        service = attrs.get("service") or self.instance.service
        package = attrs.get("package")

        # Make sure the package belongs to the service
        if package and package.service_id != service.id:
            raise serializers.ValidationError(
                {"package": "This package does not belong to the selected service."}
            )

        # Dates validation
        start = attrs.get("start_date")
        end = attrs.get("end_date")

        if start and end and end < start:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        return attrs

    def create(self, validated_data):
        """Attach the requesting user automatically."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user

        return super().create(validated_data)


# ======================================================
# NOTIFICATIONS
# ======================================================

class NotificationSerializer(serializers.ModelSerializer):
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_username",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = ("created_at",)
