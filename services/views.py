from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema

from .models import Service, Package, ServiceImage, ServiceAvailability
from .serializers import (
    ServiceSerializer,
    PackageSerializer,
    ServiceImageSerializer,
    ServiceAvailabilitySerializer,
)
from .permissions import ServicePermission, PackagePermission
from bookings.models import Booking


class ServiceViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete", "options", "head"]

    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [ServicePermission]
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        qs = Service.objects.all().prefetch_related(
            "images",
            "availabilities",
            Prefetch("packages", queryset=Package.objects.filter(is_active=True)),
        )

        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return qs

        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return qs.filter(operator=user)

        return qs.filter(is_active=True, is_approved=True)

    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()

        # Prevent deletion if active bookings exist
        active_bookings = Booking.objects.filter(
            service=service,
            status__in=[
                Booking.STATUS_PENDING,
                Booking.STATUS_PAID,
                Booking.STATUS_CONFIRMED,
            ],
        ).exists()

        if active_bookings:
            return Response(
                {
                    "detail": "This service cannot be deleted because it has active bookings."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service.is_active = False
        service.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"detail": "Service deactivated successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"}
                },
                "required": ["image"],
            }
        },
        responses=ServiceImageSerializer,
    )
    @action(
        detail=True,
        methods=["get", "post"],
        permission_classes=[IsAuthenticated],
        url_path="images",
    )
    def images(self, request, slug=None):
        service = self.get_object()

        if request.method == "POST":
            if (not request.user.is_staff) and (service.operator != request.user):
                return Response(
                    {"detail": "You do not own this service."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ServiceImageSerializer(
                data=request.data,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(service=service)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        images = service.images.all()
        serializer = ServiceImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUser],
        url_path="approve",
    )
    def approve(self, request, slug=None):
        service = self.get_object()
        service.is_approved = True
        service.save(update_fields=["is_approved"])
        return Response(
            {"detail": "Service approved successfully."},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdminUser],
        url_path="reject",
    )
    def reject(self, request, slug=None):
        service = self.get_object()
        service.is_approved = False
        service.save(update_fields=["is_approved"])
        return Response(
            {"detail": "Service rejected."},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="availability",
    )
    def availability(self, request, slug=None):
        service = self.get_object()
        availabilities = service.availabilities.filter(is_active=True)
        serializer = ServiceAvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="deactivate",
    )
    def deactivate(self, request, slug=None):
        service = self.get_object()

        if not request.user.is_staff and service.operator != request.user:
            return Response(
                {"detail": "You do not own this service."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Prevent deactivation if active bookings exist
        active_bookings = Booking.objects.filter(
            service=service,
            status__in=[
                Booking.STATUS_PENDING,
                Booking.STATUS_PAID,
                Booking.STATUS_CONFIRMED,
            ],
        ).exists()

        if active_bookings:
            return Response(
                {
                    "detail": "This service cannot be deactivated because it has active bookings."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service.is_active = False
        service.save(update_fields=["is_active", "updated_at"])

        return Response(
            {"detail": "Service deactivated successfully.", "is_active": service.is_active},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="activate",
    )
    def activate(self, request, slug=None):
        service = self.get_object()

        if not request.user.is_staff and service.operator != request.user:
            return Response(
                {"detail": "You do not own this service."},
                status=status.HTTP_403_FORBIDDEN,
            )

        service.is_active = True
        service.save(update_fields=["is_active", "updated_at"])

        return Response(
            {"detail": "Service activated successfully.", "is_active": service.is_active},
            status=status.HTTP_200_OK,
        )


class PackageViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete", "options", "head"]
    serializer_class = PackageSerializer
    permission_classes = [PackagePermission]
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Package.objects.all()

        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return Package.objects.filter(service__operator=user)

        return Package.objects.filter(service__is_active=True)

    def perform_create(self, serializer):
        """
        Enforce that operators can only add packages to their own services.
        Also guarantees packages are always attached to a service.
        """
        user = self.request.user
        service = serializer.validated_data.get("service")

        if not service:
            raise serializers.ValidationError({"service": "This field is required."})

        if getattr(user, "role", None) == "operator" and service.operator_id != user.id:
            raise serializers.ValidationError(
                {"service": "You can only add packages to your own services."}
            )

        serializer.save()


class ServiceCalendarView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        service = get_object_or_404(Service, slug=slug, is_active=True)

        calendar = {}
        availabilities = service.availabilities.filter(is_active=True)

        for availability in availabilities:
            current_date = availability.start_date

            while current_date <= availability.end_date:
                weekday = current_date.strftime("%A")

                if availability.available_days and weekday not in availability.available_days:
                    current_date += timedelta(days=1)
                    continue

                date_key = current_date.isoformat()
                calendar.setdefault(date_key, [])

                for slot in availability.time_slots.filter(is_active=True):
                    remaining = slot.seats_remaining()

                    calendar[date_key].append({
                        "time_slot_id": slot.id,
                        "start_time": slot.start_time.strftime("%H:%M"),
                        "end_time": slot.end_time.strftime("%H:%M"),
                        "capacity": slot.capacity,
                        "remaining": remaining,
                        "available": remaining > 0,
                    })

                current_date += timedelta(days=1)

        return Response({
            "service": {
                "id": service.id,
                "title": service.title,
                "slug": service.slug,
            },
            "calendar": calendar
        })