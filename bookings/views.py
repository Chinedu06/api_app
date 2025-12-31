from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Notification
from .serializers import BookingSerializer, NotificationSerializer


# ============================================================
# CREATE BOOKING
# ============================================================

class CreateBookingView(generics.CreateAPIView):
    """
    Public endpoint — allows both authenticated & guest users.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """
        If user is authenticated, attach user automatically.
        Guest users will have user=None which is allowed.
        """
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


# ============================================================
# LIST BOOKINGS FOR LOGGED-IN USER
# ============================================================

class MyBookingsView(generics.ListAPIView):
    """
    Shows bookings only for the authenticated user.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")


# ============================================================
# ADMIN — LIST ALL BOOKINGS
# (Optional, protected by staff permissions)
# ============================================================

class AllBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAdminUser]

    queryset = Booking.objects.all().order_by("-created_at")


# ============================================================
# MARK BOOKING AS READ / UPDATE STATUS (ADMIN)
# ============================================================

class UpdateBookingStatusView(APIView):
    """
    Patch endpoint:
        POST /api/bookings/<id>/status/
        { "status": "confirmed" }
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, booking_id):
        status_value = request.data.get("status")

        if status_value not in [
            Booking.STATUS_PENDING,
            Booking.STATUS_CONFIRMED,
            Booking.STATUS_CANCELLED,
        ]:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.status = status_value
        booking.save()

        return Response({"message": "Booking status updated"})


# ============================================================
# NOTIFICATION ENDPOINTS
# ============================================================

class MyNotificationsView(generics.ListAPIView):
    """
    Shows notifications for the logged-in user.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkNotificationReadView(APIView):
    """
    POST /api/notifications/<id>/read/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notif_id):
        try:
            notif = Notification.objects.get(id=notif_id, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        notif.is_read = True
        notif.save()

        return Response({"message": "Notification marked as read"})

class GuestBookingDetailView(generics.RetrieveAPIView):
    """
    Allows a guest (non-authenticated user) to retrieve
    their booking using booking ID + email.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        email = self.request.query_params.get("email")

        # No email → no access
        if not email:
            return Booking.objects.none()

        return Booking.objects.filter(email=email)

class OperatorBookingsView(generics.ListAPIView):
    """
    Allows an operator to view bookings
    made for their own services only.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Extra safety check
        if getattr(user, "role", None) != "operator":
            return Booking.objects.none()

        return Booking.objects.filter(
            service__operator=user
        ).order_by("-created_at")
