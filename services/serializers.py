from rest_framework import serializers
from .models import (
    Service,
    Package,
    ServiceImage,
    ServiceAvailability,
    ServiceTimeSlot,
)

# ---------------------------------------------------
# SERVICE IMAGE SERIALIZER
# ---------------------------------------------------
class ServiceImageSerializer(serializers.ModelSerializer):
    MAX_IMAGES = 4
    MAX_FILE_SIZE_MB = 5

    class Meta:
        model = ServiceImage
        fields = ("id", "image", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")

    def validate_image(self, image):
        max_size = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if image.size > max_size:
            raise serializers.ValidationError(
                f"Image size must be ≤ {self.MAX_FILE_SIZE_MB}MB"
            )

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]

        if image.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported file type.")

        return image

    def validate(self, attrs):
        request = self.context.get("request")
        service_slug = request.parser_context["kwargs"].get("slug")

        service = Service.objects.filter(slug=service_slug).first()
        if not service:
            raise serializers.ValidationError("Invalid service.")

        if service.images.count() >= self.MAX_IMAGES:
            raise serializers.ValidationError(
                f"Maximum of {self.MAX_IMAGES} images allowed per service."
            )

        return attrs


# ---------------------------------------------------
# TIME SLOT SERIALIZER (CHILD)
# ---------------------------------------------------
class ServiceTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTimeSlot
        fields = [
            "id",
            "start_time",
            "end_time",
            "capacity",
            "is_active",
        ]


# ---------------------------------------------------
# AVAILABILITY SERIALIZER (PARENT OF TIME SLOTS)
# ---------------------------------------------------
class ServiceAvailabilitySerializer(serializers.ModelSerializer):
    time_slots = ServiceTimeSlotSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceAvailability
        fields = [
            "id",
            "start_date",
            "end_date",
            "available_days",
            "is_active",
            "time_slots",
        ]


# ---------------------------------------------------
# PACKAGE SERIALIZER
# ---------------------------------------------------
class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "description",
            "price",
            "duration_days",
            "max_people",
            "is_active",
        ]


# ---------------------------------------------------
# SERVICE SERIALIZER (TOP-LEVEL)
# ---------------------------------------------------
class ServiceSerializer(serializers.ModelSerializer):
    packages = PackageSerializer(many=True, read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(read_only=True)
    availabilities = ServiceAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "duration_hours",
            "available_days",
            "is_active",
            "images",
            "images_count",
            "packages",
            "availabilities",
        ]
