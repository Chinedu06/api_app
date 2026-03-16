from django.urls import path
from .views import (
    CreateBookingView,
    GuestBookingDetailView,
    MyBookingsView,
    AllBookingsView,
    OperatorBookingsView,
    UpdateBookingStatusView,
    MyNotificationsView,
    MarkNotificationReadView,
    BookingVerifyView,
)

app_name = "bookings"

urlpatterns = [
    # -------------------------------
    # BOOKINGS
    # -------------------------------
    path("create/", CreateBookingView.as_view(), name="booking-create"),
    path("mine/", MyBookingsView.as_view(), name="booking-my-list"),
    path("all/", AllBookingsView.as_view(), name="booking-all"),
    path("<int:booking_id>/status/", UpdateBookingStatusView.as_view(), name="booking-update-status"),
    path("<int:id>/guest/", GuestBookingDetailView.as_view(), name="booking-guest-detail"),
    path("operator/", OperatorBookingsView.as_view(), name="booking-operator-list"),

    # -------------------------------
    # QR VERIFICATION
    # -------------------------------
    path("verify/<str:token>/", BookingVerifyView.as_view(), name="booking-verify"),

    # -------------------------------
    # NOTIFICATIONS
    # -------------------------------
    path("notifications/", MyNotificationsView.as_view(), name="notifications-list"),
    path("notifications/<int:notif_id>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
]