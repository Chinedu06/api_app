from django.urls import path
from . import views

app_name = "payments"


urlpatterns = [
    # 1) Initialize Payment
    path("init/<int:booking_id>/", views.initialize_payment, name="initialize_payment"),

    # 2) Flutterwave redirect/pages
    path("success/", views.payment_success, name="payment_success"),
    path("cancelled/", views.payment_cancelled, name="payment_cancelled"),

    # 3) Flutterwave webhook
    path("webhook/", views.flutterwave_webhook, name="flutterwave_webhook"),

    # 4) Optional status checker
    path("status/<str:reference>/", views.check_payment_status, name="check_payment_status"),
]
