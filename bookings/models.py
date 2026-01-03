from django.db import models
from django.conf import settings
from services.models import Service, Package
from django.utils import timezone
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
    RESTORED Booking model with full travel details, package selection,
    traveler info, dates, and admin workflow.
    """

    # ----------------------------
    # Booking Statuses
    # ----------------------------
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REJECTED = 'rejected'


    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    # ----------------------------
    # Payment Statuses
    # ----------------------------
    PAYMENT_UNPAID = 'unpaid'
    PAYMENT_PAID = 'paid'
    PAYMENT_PENDING = 'pending_verification'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, 'Unpaid'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_PENDING, 'Pending Verification'),
    ]

    # ----------------------------
    # User & Service
    # ----------------------------
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='bookings'
    )

    # ⭐ RESTORED — Package linking support
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
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

    # Optional file upload (proof of booking, receipts, etc.)
    proof_document = models.FileField(
        upload_to='bookings/proofs/',
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
        """Package price overrides service price."""
        if self.package:
            return self.package.price
        return self.service.price

    def __str__(self):
        return f"Booking#{self.pk} {self.service.title} for {self.given_name} {self.surname}"

    def mark_paid(self):
        """
        The ONLY allowed way to mark a booking as paid + confirmed.
        This must be called ONLY by Transaction logic.
        """
        if self.payment_status == self.PAYMENT_PAID:
            return

        self.payment_status = self.PAYMENT_PAID
        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["payment_status", "status", "updated_at"])

class Notification(models.Model):
    """
    Simple system notification table.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification#{self.pk} to {self.recipient} - {self.message[:30]}..."