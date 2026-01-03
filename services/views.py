from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Service, Package
from .serializers import ServiceSerializer, PackageSerializer
from .permissions import ServicePermission, PackagePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.shortcuts import get_object_or_404
from .models import ServiceImage
from .serializers import ServiceImageSerializer


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
    
    @action(
        detail=True,
        methods=["get", "post"],
        permission_classes=[IsAuthenticated],
        url_path="images",
    )
    def images(self, request, slug=None):
        service = self.get_object()

        # 🔒 Operators can only upload to their own service
        if request.method == "POST":
            if (
                not request.user.is_staff
                and service.operator != request.user
            ):
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

        # GET → list images
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
