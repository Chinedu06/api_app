from rest_framework import generics
from .models import Service, Package
from .serializers import ServiceSerializer, PackageSerializer


class ServiceListView(generics.ListAPIView):
    """
    Returns a list of all active services.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer


class ServiceDetailView(generics.RetrieveAPIView):
    """
    Returns details of a single service including its packages.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    lookup_field = "slug"


class PackageListView(generics.ListAPIView):
    """
    List all packages (usually used internally).
    """
    queryset = Package.objects.all()
    serializer_class = PackageSerializer


class PackageDetailView(generics.RetrieveAPIView):
    """
    Get a single package by ID.
    """
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = "id"
