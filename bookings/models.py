from django.db import models
from django.conf import settings
from services.models import Service, Package
from services.models import ServiceTimeSlot


class Booking(models.Model):
    time_slot = models.ForeignKey(
        ServiceTimeSlot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Specific time slot booked"
    )

    """
    Booking model with full travel details, package selection,
    traveler info, dates, pricing snapshots, and workflow.
    """

    # ----------------------------
    # Booking Statuses
    # ----------------------------
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # ----------------------------
    # Payment Statuses
    # ----------------------------
    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PAID = "paid"
    PAYMENT_PENDING = "pending_verification"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_PENDING, "Pending Verification"),
    ]

    # ----------------------------
    # User & Service
    # ----------------------------
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings"
    )

    # ----------------------------
    # SNAPSHOT FIELDS
    # ----------------------------
    service_title_snapshot = models.CharField(max_length=200, blank=True, default="")
    service_description_snapshot = models.TextField(blank=True, default="")
    service_inclusive_snapshot = models.TextField(blank=True, default="")
    service_duration_hours_snapshot = models.PositiveIntegerField(null=True, blank=True)

    # ----------------------------
    # PRICE SNAPSHOT FIELDS (NEW)
    # ----------------------------
    service_price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    package_price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    final_price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final booked amount at the time the booking was created."
    )

    # ----------------------------
    # Traveler & Contact Information
    # ----------------------------
    given_name = models.CharField(max_length=150)
    surname = models.CharField(max_length=150)
    other_names = models.CharField(max_length=150, blank=True)
    contact_number = models.CharField(max_length=40)
    email = models.EmailField()
    full_contact_address = models.TextField(blank=True)

    # ----------------------------
    # Booking Details
    # ----------------------------
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # ----------------------------
    # Statuses
    # ----------------------------
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID
    )

    is_tnc_accepted = models.BooleanField(default=False)

    proof_document = models.FileField(
        upload_to="bookings/proofs/",
        null=True,
        blank=True
    )

    # ----------------------------
    # Admin Fields
    # ----------------------------
    admin_note = models.TextField(blank=True)

    # ----------------------------
    # Timestamps
    # ----------------------------
    booking_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ----------------------------
    # Helpers
    # ----------------------------
    @property
    def total_price(self):
        """
        Live/computed price from current service/package.
        Kept for backward compatibility.
        """
        if self.package:
            return self.package.price
        return self.service.price

    @property
    def booked_total_price(self):
        """
        Stable historical price captured at booking time.
        Falls back safely if snapshot is missing on older records.
        """
        if self.final_price_snapshot is not None:
            return self.final_price_snapshot
        if self.package_price_snapshot is not None:
            return self.package_price_snapshot
        if self.service_price_snapshot is not None:
            return self.service_price_snapshot
        return self.total_price

    def __str__(self):
        return f"Booking#{self.pk} {self.service.title} for {self.given_name} {self.surname}"

    def mark_paid(self):
        """
        Payment confirmed (gateway success or admin-approved bank transfer).
        IMPORTANT: This does NOT auto-confirm the booking.
        Operator must confirm after payment.
        """
        if self.payment_status == self.PAYMENT_PAID:
            return

        self.payment_status = self.PAYMENT_PAID
        self.status = self.STATUS_PAID
        self.save(update_fields=["payment_status", "status", "updated_at"])


class Notification(models.Model):
    """
    Simple system notification table (DO NOT REMOVE/REPLACE).
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification#{self.pk} to {self.recipient} - {self.message[:30]}..."