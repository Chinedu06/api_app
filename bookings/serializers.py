# from rest_framework import serializers
# from .models import Booking, Notification
# from services.models import ServiceTimeSlot


# class ServiceTimeSlotMiniSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ServiceTimeSlot
#         fields = ["id", "start_time", "end_time"]


# class BookingSerializer(serializers.ModelSerializer):
#     """
#     Serializer for creating and viewing bookings.
#     Includes personal details + package + service + snapshots.
#     """

#     service_title = serializers.CharField(source="service.title", read_only=True)
#     package_name = serializers.CharField(source="package.name", read_only=True)

#     time_slot = ServiceTimeSlotMiniSerializer(read_only=True)

#     time_slot_id = serializers.PrimaryKeyRelatedField(
#         queryset=ServiceTimeSlot.objects.filter(is_active=True),
#         source="time_slot",
#         write_only=True,
#         required=False,
#         allow_null=True,
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

#             # NEW snapshots (stored in Booking)
#             "service_title_snapshot",
#             "service_description_snapshot",
#             "service_inclusive_snapshot",
#             "service_duration_hours_snapshot",

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

#             # Slot booking
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

#             # snapshots are backend-owned
#             "service_title_snapshot",
#             "service_description_snapshot",
#             "service_inclusive_snapshot",
#             "service_duration_hours_snapshot",
#         )

#     def validate(self, attrs):
#         time_slot = attrs.get("time_slot")

#         service = attrs.get("service") or (self.instance.service if self.instance else None)
#         if service is None:
#             raise serializers.ValidationError({"service": "Service is required."})

#         package = attrs.get("package")

#         start_date = attrs.get("start_date") or (self.instance.start_date if self.instance else None)
#         end_date = attrs.get("end_date") or (self.instance.end_date if self.instance else None)

#         if time_slot is None and not (start_date and end_date):
#             raise serializers.ValidationError(
#                 "Either time_slot_id or start_date & end_date must be provided."
#             )

#         if package and package.service_id != service.id:
#             raise serializers.ValidationError(
#                 {"package": "This package does not belong to the selected service."}
#             )

#         if start_date and end_date and end_date < start_date:
#             raise serializers.ValidationError({"end_date": "End date cannot be before start date."})

#         if time_slot is not None:
#             slot_service_id = time_slot.availability.service_id
#             if slot_service_id != service.id:
#                 raise serializers.ValidationError(
#                     {"time_slot_id": "This time slot does not belong to the selected service."}
#                 )

#             adults = attrs.get("num_adults", 0)
#             children = attrs.get("num_children", 0)
#             requested_seats = adults + children

#             if requested_seats <= 0:
#                 raise serializers.ValidationError({"num_adults": "At least one traveler is required."})

#             remaining = time_slot.seats_remaining()
#             if remaining < requested_seats:
#                 raise serializers.ValidationError(
#                     {"time_slot_id": f"Not enough capacity. {remaining} seats remaining."}
#                 )

#         return attrs

#     def create(self, validated_data):
#         """
#         Attach user if authenticated AND store service snapshots.
#         """
#         request = self.context.get("request")
#         if request and request.user and request.user.is_authenticated:
#             validated_data["user"] = request.user

#         service = validated_data.get("service")
#         if service:
#             # snapshots always stored at booking time
#             validated_data["service_title_snapshot"] = getattr(service, "title", "") or ""
#             validated_data["service_description_snapshot"] = getattr(service, "description", "") or ""
#             validated_data["service_duration_hours_snapshot"] = getattr(service, "duration_hours", None)

#             # Will work once Service.tour_inclusive exists (safe now)
#             validated_data["service_inclusive_snapshot"] = getattr(service, "tour_inclusive", "") or ""

#         return super().create(validated_data)


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
    Includes personal details + package + service + snapshots.
    """

    service_title = serializers.CharField(source="service.title", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)

    time_slot = ServiceTimeSlotMiniSerializer(read_only=True)

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

            # Service snapshots
            "service_title_snapshot",
            "service_description_snapshot",
            "service_inclusive_snapshot",
            "service_duration_hours_snapshot",

            # Price snapshots
            "service_price_snapshot",
            "package_price_snapshot",
            "final_price_snapshot",

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

            # backend-owned snapshots
            "service_title_snapshot",
            "service_description_snapshot",
            "service_inclusive_snapshot",
            "service_duration_hours_snapshot",
            "service_price_snapshot",
            "package_price_snapshot",
            "final_price_snapshot",
        )

    def validate(self, attrs):
        time_slot = attrs.get("time_slot")

        service = attrs.get("service") or (self.instance.service if self.instance else None)
        if service is None:
            raise serializers.ValidationError({"service": "Service is required."})

        package = attrs.get("package")

        start_date = attrs.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date = attrs.get("end_date") or (self.instance.end_date if self.instance else None)

        if time_slot is None and not (start_date and end_date):
            raise serializers.ValidationError(
                "Either time_slot_id or start_date & end_date must be provided."
            )

        if package and package.service_id != service.id:
            raise serializers.ValidationError(
                {"package": "This package does not belong to the selected service."}
            )

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be before start date."}
            )

        if time_slot is not None:
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
                    {"time_slot_id": f"Not enough capacity. {remaining} seats remaining."}
                )

        return attrs

    def create(self, validated_data):
        """
        Attach user if authenticated AND store stable snapshots.
        """
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user

        service = validated_data.get("service")
        package = validated_data.get("package")

        if service:
            validated_data["service_title_snapshot"] = getattr(service, "title", "") or ""
            validated_data["service_description_snapshot"] = getattr(service, "description", "") or ""
            validated_data["service_duration_hours_snapshot"] = getattr(service, "duration_hours", None)
            validated_data["service_inclusive_snapshot"] = getattr(service, "tour_inclusive", "") or ""
            validated_data["service_price_snapshot"] = getattr(service, "price", None)

        package_price = None
        if package:
            package_price = getattr(package, "price", None)
            validated_data["package_price_snapshot"] = package_price

        service_price = validated_data.get("service_price_snapshot")
        validated_data["final_price_snapshot"] = package_price if package_price is not None else service_price

        return super().create(validated_data)


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