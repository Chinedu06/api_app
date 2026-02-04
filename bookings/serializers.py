# from rest_framework import serializers
# from .models import Booking, Notification
# from services.models import Package, Service
# from services.models import ServiceTimeSlot

# class ServiceTimeSlotMiniSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceTimeSlot
#         fields = ["id", "start_time", "end_time"]

# class BookingSerializer(serializers.ModelSerializer):
#     """
#     Serializer for creating and viewing bookings.
#     Includes full personal details + package + service.
#     """

#     service_title = serializers.CharField(source="service.title", read_only=True)
#     package_name = serializers.CharField(source="package.name", read_only=True)
#     time_slot = ServiceTimeSlotMiniSerializer(read_only=True)
#     time_slot_id = serializers.PrimaryKeyRelatedField(
#         queryset=ServiceTimeSlot.objects.all(),
#         source="time_slot",
#         write_only=True,
#         required=False,
#         allow_null=True
#     )


#     class Meta:
#         model = Booking
#         fields = [
#             "id",
#             "user",
#             "service",
#             "service_title",
#             "package",
#             "package_name",

#             # Personal details
#             "given_name",
#             "surname",
#             "other_names",
#             "contact_number",
#             "email",
#             "full_contact_address",

#             # Travelers
#             "num_adults",
#             "num_children",

#             # Trip dates
#             "start_date",
#             "end_date",

#             # Notes
#             "notes",
#             "admin_note",

#             # Status + Payment
#             "status",
#             "payment_status",

#             # Timestamps
#             "created_at",
#             "updated_at",

#             "time_slot",
#             "time_slot_id",
#         ]
#         read_only_fields = (
#             "status",
#             "payment_status",
#             "created_at",
#             "updated_at",
#             "admin_note",
#             "user",
#         )

#     # ============================================
#     # VALIDATION
#     # ============================================



#     def validate(self, attrs):

#         time_slot = attrs.get("time_slot")
#         start_date = attrs.get("start_date")
#         end_date = attrs.get("end_date")
#         service = attrs.get("service") or self.instance.service
#         package = attrs.get("package")

#         if not time_slot and not (start_date and end_date):
#             raise serializers.ValidationError(
#                 "Either time_slot_id or start_date & end_date must be provided."
#             )

#         # Make sure the package belongs to the service
#         if package and package.service_id != service.id:
#             raise serializers.ValidationError(
#                 {"package": "This package does not belong to the selected service."}
#             )

#         # Dates validation
#         start = attrs.get("start_date")
#         end = attrs.get("end_date")

#         if start and end and end < start:
#             raise serializers.ValidationError(
#                 {"end_date": "End date cannot be before start date."}
#             )

#         if time_slot:
#             adults = attrs.get("num_adults", 0)
#             children = attrs.get("num_children", 0)
#             requested_seats = adults + children

#         if requested_seats <= 0:
#             raise serializers.ValidationError(
#                 {"num_adults": "At least one traveler is required."}
#             )

#         if time_slot.seats_remaining() < requested_seats:
#             raise serializers.ValidationError(
#                 {
#                     "time_slot_id": (
#                         "Not enough capacity for this time slot. "
#                         f"{time_slot.seats_remaining()} seats remaining."
#                     )
#                 }
#             )

#         return attrs

#     def create(self, validated_data):
#         """Attach the requesting user automatically."""
#         request = self.context.get("request")
#         if request and request.user.is_authenticated:
#             validated_data["user"] = request.user

#         return super().create(validated_data)


# # ======================================================
# # NOTIFICATIONS
# # ======================================================

# class NotificationSerializer(serializers.ModelSerializer):
#     recipient_username = serializers.CharField(source="recipient.username", read_only=True)

#     class Meta:
#         model = Notification
#         fields = [
#             "id",
#             "recipient",
#             "recipient_username",
#             "message",
#             "is_read",
#             "created_at",
#         ]
#         read_only_fields = ("created_at",)

from rest_framework import serializers
from .models import Booking, Notification
from services.models import ServiceTimeSlot


class ServiceTimeSlotMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTimeSlot
        fields = ["id", "start_time", "end_time"]


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing bookings.
    Includes full personal details + package + service.
    """

    service_title = serializers.CharField(source="service.title", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)

    time_slot = ServiceTimeSlotMiniSerializer(read_only=True)

    # Fix 1: allow null AND restrict to active slots
    time_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceTimeSlot.objects.filter(is_active=True),
        source="time_slot",
        write_only=True,
        required=False,
        allow_null=True,
    )

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

            # Slot booking
            "time_slot",
            "time_slot_id",
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
        """
        Supports BOTH:
        - Slot-based bookings (time_slot_id provided)
        - Legacy date bookings (start_date/end_date only)
        Prevents 500 errors and enforces capacity for slot bookings.
        """

        time_slot = attrs.get("time_slot")

        # Fix 2: resolve service safely (prevents self.instance None crash)
        service = attrs.get("service") or (self.instance.service if self.instance else None)
        if service is None:
            raise serializers.ValidationError({"service": "Service is required."})

        package = attrs.get("package")

        # Rule: require either a slot OR start/end dates
        start_date = attrs.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date = attrs.get("end_date") or (self.instance.end_date if self.instance else None)

        if time_slot is None and not (start_date and end_date):
            raise serializers.ValidationError(
                "Either time_slot_id or start_date & end_date must be provided."
            )

        # Package must belong to service
        if package and package.service_id != service.id:
            raise serializers.ValidationError(
                {"package": "This package does not belong to the selected service."}
            )

        # Date validation
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        # Slot-mode validation (capacity + ownership)
        if time_slot is not None:
            # Ensure slot belongs to this service
            slot_service_id = time_slot.availability.service_id
            if slot_service_id != service.id:
                raise serializers.ValidationError(
                    {"time_slot_id": "This time slot does not belong to the selected service."}
                )

            adults = attrs.get("num_adults", 0)
            children = attrs.get("num_children", 0)
            requested_seats = adults + children

            if requested_seats <= 0:
                raise serializers.ValidationError(
                    {"num_adults": "At least one traveler is required."}
                )

            remaining = time_slot.seats_remaining()
            if remaining < requested_seats:
                raise serializers.ValidationError(
                    {
                        "time_slot_id": (
                            "Not enough capacity for this time slot. "
                            f"{remaining} seats remaining."
                        )
                    }
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

