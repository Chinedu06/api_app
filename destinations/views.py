from rest_framework import generics, permissions
from .models import Destination
from .serializers import DestinationSerializer


class DestinationListView(generics.ListAPIView):
    """
    Public list of active destinations for dropdowns.
    """
    serializer_class = DestinationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Destination.objects.filter(is_active=True).order_by("sort_order", "country", "city")