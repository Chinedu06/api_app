from django.http import HttpResponse

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Notification
from .serializers import BookingSerializer, NotificationSerializer


class CreateBookingView(generics.CreateAPIView):
    """
    Public endpoint — allows both authenticated & guest users.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


class MyBookingsView(generics.ListAPIView):
    """
    Shows bookings only for the authenticated user.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")


class AllBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Booking.objects.all().order_by("-created_at")


class UpdateBookingStatusView(APIView):
    """
    POST /api/v1/bookings/<id>/status/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        new_status = request.data.get("status")
        reason = request.data.get("reason", "").strip()

        allowed_statuses = {
            Booking.STATUS_PENDING,
            Booking.STATUS_CONFIRMED,
            Booking.STATUS_CANCELLED,
            Booking.STATUS_REJECTED,
            Booking.STATUS_PAID,
        }

        if new_status not in allowed_statuses:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking.objects.select_related("service__operator").get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        user = request.user
        is_admin = user.is_staff or user.is_superuser
        is_operator_owner = (
            getattr(user, "role", None) == "operator"
            and booking.service.operator_id == user.id
        )

        if not (is_admin or is_operator_owner):
            return Response(
                {"detail": "You do not have permission to update this booking."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if is_operator_owner and new_status == Booking.STATUS_CONFIRMED:
            if booking.payment_status != Booking.PAYMENT_PAID:
                return Response(
                    {
                        "detail": "Cannot confirm booking until payment is marked as PAID.",
                        "payment_status": booking.payment_status,
                        "status": booking.status,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if is_operator_owner and new_status == Booking.STATUS_PAID:
            return Response(
                {"detail": "Operators cannot mark bookings as PAID. Payment is set by gateway/admin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        booking.status = new_status

        update_fields = ["status", "updated_at"]

        if new_status == Booking.STATUS_REJECTED and reason:
            booking.admin_note = reason
            update_fields.append("admin_note")

        booking.save(update_fields=update_fields)

        return Response(
            {
                "message": "Booking status updated successfully",
                "status": booking.status,
                "booking_status": booking.status,
                "payment_status": booking.payment_status,
                "admin_note": booking.admin_note,
            },
            status=status.HTTP_200_OK,
        )


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
        notif.save(update_fields=["is_read"])

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

        if getattr(user, "role", None) != "operator":
            return Booking.objects.none()

        return Booking.objects.filter(service__operator=user).order_by("-created_at")


class BookingVerifyView(APIView):
    """
    Public verification endpoint used by QR scans.

    Returns:
    - JSON if ?format=json is used or Accept: application/json
    - Human-readable HTML page otherwise
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        try:
            booking = Booking.objects.select_related(
                "service",
                "package",
                "payment",
            ).get(booking_qr_token=token)
        except Booking.DoesNotExist:
            return self._render_invalid(
                request,
                "Booking not found or invalid QR token.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reasons = []

        if booking.status == Booking.STATUS_CANCELLED:
            reasons.append("Booking has been cancelled.")

        if booking.status == Booking.STATUS_REJECTED:
            reasons.append("Booking has been rejected.")

        if booking.payment_status != Booking.PAYMENT_PAID:
            reasons.append("Payment has not been completed.")

        if booking.status != Booking.STATUS_CONFIRMED:
            reasons.append("Booking has not been confirmed by the operator.")

        is_valid = booking.is_qr_verification_valid and not reasons

        payload = {
            "valid": is_valid,
            "booking_id": booking.id,
            "tourist_name": f"{booking.given_name} {booking.surname}".strip(),
            "tour_title": booking.service_title_snapshot or booking.service.title,
            "package": booking.package.name if booking.package else None,
            "start_date": booking.start_date,
            "end_date": booking.end_date,
            "booking_status": booking.status,
            "payment_status": booking.payment_status,
            "final_booked_price": booking.final_price_snapshot,
            "payment_provider": getattr(getattr(booking, "payment", None), "provider", None),
            "payment_reference": getattr(getattr(booking, "payment", None), "reference", None),
            "payment_paid_at": getattr(getattr(booking, "payment", None), "paid_at", None),
            "reason": None if is_valid else " ".join(reasons),
        }

        wants_json = (
            request.query_params.get("format") == "json"
            or "application/json" in request.headers.get("Accept", "")
        )

        if wants_json:
            return Response(payload, status=status.HTTP_200_OK)

        return self._render_html(payload)

    def _render_invalid(self, request, message, status_code=404):
        wants_json = (
            request.query_params.get("format") == "json"
            or "application/json" in request.headers.get("Accept", "")
        )

        payload = {
            "valid": False,
            "reason": message,
        }

        if wants_json:
            return Response(payload, status=status_code)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Booking Verification</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f8f9fb;
                    margin: 0;
                    padding: 24px;
                    color: #1f2937;
                }}
                .card {{
                    max-width: 680px;
                    margin: 40px auto;
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
                }}
                .badge-invalid {{
                    display: inline-block;
                    padding: 8px 12px;
                    border-radius: 999px;
                    background: #fee2e2;
                    color: #991b1b;
                    font-weight: bold;
                    margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="badge-invalid">Invalid Booking</div>
                <h2>Booking Verification Failed</h2>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, status=status_code)

    def _render_html(self, payload):
        badge_class = "badge-valid" if payload["valid"] else "badge-invalid"
        badge_text = "Valid Booking" if payload["valid"] else "Invalid Booking"
        reason_html = (
            f"<p><strong>Reason:</strong> {payload['reason']}</p>"
            if payload.get("reason")
            else ""
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Booking Verification</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f8f9fb;
                    margin: 0;
                    padding: 24px;
                    color: #1f2937;
                }}
                .card {{
                    max-width: 760px;
                    margin: 40px auto;
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
                }}
                .{badge_class} {{
                    display: inline-block;
                    padding: 8px 12px;
                    border-radius: 999px;
                    font-weight: bold;
                    margin-bottom: 16px;
                    background: {"#dcfce7" if payload["valid"] else "#fee2e2"};
                    color: {"#166534" if payload["valid"] else "#991b1b"};
                }}
                .row {{
                    margin: 10px 0;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .label {{
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="{badge_class}">{badge_text}</div>
                <h2>Booking Verification Result</h2>

                {reason_html}

                <div class="row"><span class="label">Booking ID:</span> {payload.get("booking_id")}</div>
                <div class="row"><span class="label">Tourist:</span> {payload.get("tourist_name")}</div>
                <div class="row"><span class="label">Tour:</span> {payload.get("tour_title")}</div>
                <div class="row"><span class="label">Package:</span> {payload.get("package") or "N/A"}</div>
                <div class="row"><span class="label">Start Date:</span> {payload.get("start_date")}</div>
                <div class="row"><span class="label">End Date:</span> {payload.get("end_date") or "N/A"}</div>
                <div class="row"><span class="label">Booking Status:</span> {payload.get("booking_status")}</div>
                <div class="row"><span class="label">Payment Status:</span> {payload.get("payment_status")}</div>
                <div class="row"><span class="label">Final Booked Price:</span> {payload.get("final_booked_price")}</div>
                <div class="row"><span class="label">Payment Provider:</span> {payload.get("payment_provider") or "N/A"}</div>
                <div class="row"><span class="label">Payment Reference:</span> {payload.get("payment_reference") or "N/A"}</div>
                <div class="row"><span class="label">Paid At:</span> {payload.get("payment_paid_at") or "N/A"}</div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, status=200)