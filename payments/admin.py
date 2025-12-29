from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Transaction, Payment
from .services import retry_gateway_verification


# =====================================================================
# TRANSACTION ADMIN
# =====================================================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "booking_link",
        "provider",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("provider", "status", "created_at")
    search_fields = ("reference", "booking__id", "flutterwave_id")
    readonly_fields = ("created_at", "updated_at", "meta_pretty")
    actions = ["mark_success", "retry_verification"]

    # ---------------------------
    # BOOKING LINK (READ-ONLY)
    # ---------------------------
    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html(f"<a href='{url}'>Booking #{obj.booking.id}</a>")
    booking_link.short_description = "Booking"

    # ---------------------------
    # PRETTY JSON METADATA
    # ---------------------------
    def meta_pretty(self, obj):
        if not obj.meta:
            return "(empty)"
        import json
        return format_html(
            "<pre style='white-space:pre-wrap'>{}</pre>",
            json.dumps(obj.meta, indent=2),
        )
    meta_pretty.short_description = "Metadata"

    # ---------------------------
    # BULK ACTIONS
    # ---------------------------
    @admin.action(description="Mark selected transactions as SUCCESS")
    def mark_success(self, request, queryset):
        for txn in queryset:
            try:
                txn.mark_successful()
                self.message_user(request, f"{txn.reference}: Marked as successful.")
            except Exception as e:
                self.message_user(
                    request,
                    f"Error processing {txn.reference}: {e}",
                    level="error",
                )

    @admin.action(description="Retry verification with Flutterwave")
    def retry_verification(self, request, queryset):
        for txn in queryset:
            try:
                result = retry_gateway_verification(txn)
                self.message_user(request, f"{txn.reference}: {result}")
            except Exception as e:
                self.message_user(
                    request,
                    f"Error verifying {txn.reference}: {e}",
                    level="error",
                )


# =====================================================================
# PAYMENT ADMIN
# =====================================================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "booking_link",
        "reference",
        "amount",
        "provider",
        "status",
        "paid_at",
    )
    list_filter = ("provider", "status", "paid_at")
    search_fields = ("reference", "booking__id")
    readonly_fields = ("paid_at",)

    def booking_link(self, obj):
        url = reverse("admin:bookings_booking_change", args=[obj.booking.id])
        return format_html(f"<a href='{url}'>Booking #{obj.booking.id}</a>")
    booking_link.short_description = "Booking"
