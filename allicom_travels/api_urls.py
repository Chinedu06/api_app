from django.urls import path, include

urlpatterns = [
    path("api/users/", include("users.urls", namespace="users")),
    path("api/services/", include("services.urls", namespace="services")),
    path("api/bookings/", include("bookings.urls", namespace="bookings")),
    path("api/payments/", include("payments.urls", namespace="payments")),
]
