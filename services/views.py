from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Service, Package
from .serializers import ServiceSerializer, PackageSerializer
from .permissions import ServicePermission, PackagePermission
from rest_framework_simplejwt.authentication import JWTAuthentication


class ServiceViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete", "options", "head"]

    serializer_class = ServiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [ServicePermission]
    parser_classes = (MultiPartParser, FormParser)
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Service.objects.all()

        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return Service.objects.filter(operator=user)

        return Service.objects.filter(is_active=True, is_approved=True)

    def perform_create(self, serializer):
        serializer.save(operator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        service.is_active = False
        service.save(update_fields=["is_active"])
        return Response(
            {"detail": "Service deactivated successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class PackageViewSet(viewsets.ModelViewSet):
    serializer_class = PackageSerializer
    permission_classes = [PackagePermission]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Package.objects.all()

        if user.is_authenticated and getattr(user, "role", None) == "operator":
            return Package.objects.filter(service__operator=user)

        return Package.objects.filter(service__is_active=True)

    def perform_create(self, serializer):
        serializer.save()
