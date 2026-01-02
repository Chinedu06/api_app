from rest_framework import serializers
from .models import Service, Package, ServiceImage


# ---------------------------------------------------
# SERVICE IMAGE SERIALIZER (MUST COME FIRST)
# ---------------------------------------------------
class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ["id", "image", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]

    def validate_image(self, image):
        # ✅ File size (max 5MB)
        max_size = 5 * 1024 * 1024
        if image.size > max_size:
            raise serializers.ValidationError("Image size must be under 5MB.")

        # ✅ Allowed MIME types
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]
        if image.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPG, PNG, and WEBP images are allowed."
            )

        return image



# ---------------------------------------------------
# PACKAGE SERIALIZER (FIXED TO MATCH MODEL)
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
# SERVICE SERIALIZER (USES IMAGE + PACKAGE SERIALIZERS)
# ---------------------------------------------------
class ServiceSerializer(serializers.ModelSerializer):
    packages = PackageSerializer(many=True, read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    images_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "is_active",
            "images",
            "images_count",
            "packages",
        ]
