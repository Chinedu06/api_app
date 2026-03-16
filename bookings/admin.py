from django.contrib import admin
from django.utils.html import format_html

from .models import Booking, Notification
from payments.models import Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "service",
        "time_slot",
        "user",
        "status",
        "payment_status",
        "final_price_snapshot",
        "created_at",
        "payment_reference",
    )

    list_filter = ("status", "payment_status", "created_at")
    search_fields = (
        "id",
        "user__username",
        "service__title",
        "given_name",
        "surname",
        "email",
        "contact_number",
    )

    readonly_fields = (
        "service_title_snapshot",
        "service_description_snapshot",
        "service_inclusive_snapshot",
        "service_duration_hours_snapshot",
        "service_price_snapshot",
        "package_price_snapshot",
        "final_price_snapshot",
        "payment_summary",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Booking Details", {
            "fields": (
                "service",
                "package",
                "user",
                "time_slot",

                "given_name",
                "surname",
                "other_names",
                "contact_number",
                "email",
                "full_contact_address",

                "num_adults",
                "num_children",

                "start_date",
                "end_date",

                "notes",
            )
        }),

        ("Tour Snapshot (Read Only)", {
            "classes": ("collapse",),
            "fields": (
                "service_title_snapshot",
                "service_description_snapshot",
                "service_inclusive_snapshot",
                "service_duration_hours_snapshot",
            )
        }),

        ("Price Snapshot (Read Only)", {
            "fields": (
                "service_price_snapshot",
                "package_price_snapshot",
                "final_price_snapshot",
            )
        }),

        ("Status", {
            "fields": (
                "status",
                "payment_status",
                "admin_note",
            )
        }),

        ("Payment Summary (Read Only)", {
            "classes": ("collapse",),
            "fields": ("payment_summary",)
        }),

        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def payment_reference(self, obj):
        if hasattr(obj, "payment") and obj.payment.reference:
            return obj.payment.reference
        return "—"
    payment_reference.short_description = "Pay Ref"

    def payment_summary(self, obj):
        if not hasattr(obj, "payment"):
            return "No payment record."

        p: Payment = obj.payment

        return format_html(
            "<b>Status:</b> {}<br>"
            "<b>Reference:</b> {}<br>"
            "<b>Amount:</b> {}<br>"
            "<b>Provider:</b> {}<br>"
            "<b>Paid At:</b> {}",
            p.status,
            p.reference or "—",
            p.amount,
            p.provider or "—",
            p.paid_at or "—",
        )
    payment_summary.short_description = "Payment Summary"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient_display", "short_message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("recipient__username", "message")
    actions = ["mark_as_read", "mark_as_unread"]
    list_per_page = 20

    def short_message(self, obj):
        return (obj.message[:50] + "...") if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message"

    def recipient_display(self, obj):
        return obj.recipient.username if obj.recipient else "Admin / All"
    recipient_display.short_description = "Recipient"

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")

    @admin.action(description="Mark selected notifications as unread")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")