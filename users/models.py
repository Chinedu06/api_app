from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_OPERATOR = 'operator'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_OPERATOR, 'Tour Operator'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_OPERATOR,
        help_text="Designates the role of the user in the platform."
    )

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Admin approval for Operators

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class SupplierProfile(models.Model):
    """
    Operator's supplier profile — created/managed by the operator (after admin approval).
    Files uploaded to MEDIA_ROOT/supplier_certificates/.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    trading_name = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    business_address = models.TextField(blank=True)
    business_phone = models.CharField(max_length=30, blank=True)
    business_email = models.EmailField(blank=True)

    owner_full_name = models.CharField(max_length=255, blank=True)
    owner_phone = models.CharField(max_length=30, blank=True)
    owner_email = models.EmailField(blank=True)

    contact_person_name = models.CharField(max_length=255, blank=True)
    contact_person_phone = models.CharField(max_length=30, blank=True)
    contact_person_email = models.EmailField(blank=True)

    association_certificate = models.FileField(upload_to='supplier_certificates/', blank=True, null=True)
    business_certificate = models.FileField(upload_to='supplier_certificates/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SupplierProfile({self.user.username})"
