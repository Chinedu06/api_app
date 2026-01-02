from django.urls import path, include

urlpatterns = [
    path("users/", include("users.urls", namespace="users")),
    path("services/", include("services.urls", namespace="services")),
    path("bookings/", include("bookings.urls", namespace="bookings")),
    path("payments/", include("payments.urls", namespace="payments")),
]
