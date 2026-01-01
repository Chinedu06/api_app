from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Service, Package
from .serializers import ServiceSerializer, PackageSerializer
from .permissions import ServicePermission, PackagePermission


class ServiceViewSet(viewsets.ModelViewSet):
    """
    Services (Tours)

    - Public: GET approved & active services
    - Operators: create & manage their own services
    - Admin: full access
    """

    serializer_class = ServiceSerializer
    permission_classes = [ServicePermission]
    lookup_field = "slug"  # 🔑 KEEP SLUG BEHAVIOR

    def get_queryset(self):
        user = self.request.user

        # Admin sees everything
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Service.objects.all()

        # Operator sees own services
        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return Service.objects.filter(operator=user)

        # Public users
        return Service.objects.filter(is_active=True, is_approved=True)

    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete (industry standard)
        """
        service = self.get_object()
        service.is_active = False
        service.save(update_fields=["is_active"])
        return Response(
            {"detail": "Service deactivated successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class PackageViewSet(viewsets.ModelViewSet):
    """
    Packages under a Service
    """

    serializer_class = PackageSerializer
    permission_classes = [PackagePermission]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Package.objects.all()

        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return Package.objects.filter(service__operator=user)

        return Package.objects.filter(service__is_active=True)

    def perform_create(self, serializer):
        serializer.save()
