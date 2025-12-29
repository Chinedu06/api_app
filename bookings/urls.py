from django.urls import path
from .views import (
    CreateBookingView,
    MyBookingsView,
    AllBookingsView,
    UpdateBookingStatusView,
    MyNotificationsView,
    MarkNotificationReadView,
)

app_name = "bookings"


urlpatterns = [
    # -------------------------------
    # BOOKINGS
    # -------------------------------
    path("create/", CreateBookingView.as_view(), name="booking-create"),
    path("mine/", MyBookingsView.as_view(), name="booking-my-list"),
    path("all/", AllBookingsView.as_view(), name="booking-all"),  # admin only
    path("<int:booking_id>/status/", UpdateBookingStatusView.as_view(), name="booking-update-status"),

    # -------------------------------
    # NOTIFICATIONS
    # -------------------------------
    path("notifications/", MyNotificationsView.as_view(), name="notifications-list"),
    path("notifications/<int:notif_id>/read/", MarkNotificationReadView.as_view(), name="notification-read"),
]
