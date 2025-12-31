from django.urls import path
from . import views
from . import webhooks

from payments.bank_transfer_views import (
    initiate_bank_transfer,
    upload_bank_receipt,
    approve_bank_transfer,
    reject_bank_transfer,
)


app_name = "payments"


urlpatterns = [
    # 1) Initialize Payment
    path("init/<int:booking_id>/", views.initialize_payment, name="initialize_payment"),

    # 2) Flutterwave redirect/pages
    path("success/", views.payment_success, name="payment_success"),
    path("cancelled/", views.payment_cancelled, name="payment_cancelled"),

    # 3) Flutterwave webhook
    path("webhook/", views.flutterwave_webhook, name="flutterwave_webhook"),
    path("webhooks/flutterwave/", webhooks.flutterwave_webhook),

    # 4) Optional status checker
    path("status/<str:reference>/", views.check_payment_status, name="check_payment_status"),

    # Bank transfer
    path("bank/init/<int:booking_id>/", initiate_bank_transfer),
    path("bank/receipt/<str:reference>/", upload_bank_receipt),
    path("bank/approve/<str:reference>/", approve_bank_transfer),
    path("bank/reject/<str:reference>/", reject_bank_transfer),

]
