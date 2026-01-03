from rest_framework import serializers
from .models import Service, Package, ServiceImage


# ---------------------------------------------------
# SERVICE IMAGE SERIALIZER (MUST COME FIRST)
# ---------------------------------------------------
class ServiceImageSerializer(serializers.ModelSerializer):
    MAX_IMAGES = 4
    MAX_FILE_SIZE_MB = 5

    class Meta:
        model = ServiceImage
        fields = ("id", "image", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")

    def validate_image(self, image):
        # ✅ File size validation
        max_size = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if image.size > max_size:
            raise serializers.ValidationError(
                f"Image size must be ≤ {self.MAX_FILE_SIZE_MB}MB"
            )

        # ✅ MIME type validation
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
            # add these ONLY if you truly want them
            # "application/pdf",
            # "text/plain",
        ]

        content_type = image.content_type
        if content_type not in allowed_types:
            raise serializers.ValidationError(
                "Unsupported file type."
            )

        return image

    def validate(self, attrs):
        request = self.context.get("request")
        service = request.parser_context["kwargs"].get("slug")

        service_obj = Service.objects.filter(slug=service).first()
        if not service_obj:
            raise serializers.ValidationError("Invalid service.")

        # ✅ Enforce max 4 images
        if service_obj.images.count() >= self.MAX_IMAGES:
            raise serializers.ValidationError(
                f"Maximum of {self.MAX_IMAGES} images allowed per service."
            )

        return attrs




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
