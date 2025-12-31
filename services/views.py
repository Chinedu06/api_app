from rest_framework import generics
from .models import Service, Package
from .serializers import ServiceSerializer, PackageSerializer
from .permissions import ServicePermission, PackagePermission


class ServiceListView(generics.ListAPIView):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [ServicePermission]


class ServiceDetailView(generics.RetrieveAPIView):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    lookup_field = "slug"
    permission_classes = [ServicePermission]


class PackageListView(generics.ListAPIView):
    queryset = Package.objects.select_related("service")
    serializer_class = PackageSerializer
    permission_classes = [PackagePermission]


class PackageDetailView(generics.RetrieveAPIView):
    queryset = Package.objects.select_related("service")
    serializer_class = PackageSerializer
    lookup_field = "id"
    permission_classes = [PackagePermission]
