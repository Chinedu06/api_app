import uuid
import os
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError


def service_image_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("services/images/", filename)


def service_document_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("services/documents/", filename)

class Service(models.Model):
    """
    Represents a tour/service uploaded by an operator (Tour Operator).
    Matches the supplier upload form fields.
    """
    CATEGORY_CHOICES = [
        ('tour', 'Tour'),
        ('hotel', 'Hotel'),
        ('car', 'Car Hire'),
        ('restaurant', 'Restaurant'),
        ('event', 'Event'),
        ('other', 'Other'),
    ]

    # ✅ Constant for checkbox options (used by serializer validation)
    WEEKDAYS = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='tour')
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    duration_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Duration of the tour in hours"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)

    # Keep JSONField for checkboxes; serializer validates items are from WEEKDAYS
    available_days = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available weekdays (e.g. ['Monday', 'Tuesday'])"
    )

    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # Ensure uniqueness by appending a number if slug already exists
            while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def images_count(self):
        return self.images.count()

    def __str__(self):
        return f"{self.title} by {self.operator.username}"


class ServiceImage(models.Model):
    """
    Images for a service (JPEG, PNG, WEBP only)
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=service_image_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.service.title}"


class ServiceDocument(models.Model):
    """
    Optional documents (PDF, TXT)
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=service_document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for {self.service.title}"

class ServiceAvailability(models.Model):
    """
    Defines WHEN a service runs (date range + optional weekdays).
    Does NOT handle time-of-day or capacity.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    # Optional weekday restriction
    available_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Restrict to weekdays e.g. ['Monday', 'Friday']"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("start_date",)

    def __str__(self):
        return f"{self.service.title} ({self.start_date} → {self.end_date})"

    def clean(self):
        """
        Prevent overlapping availability ranges for the same service.
        """
        overlapping = ServiceAvailability.objects.filter(
            service=self.service,
            is_active=True,
        ).exclude(pk=self.pk).filter(
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        )

        if overlapping.exists():
            raise ValidationError(
                "This availability overlaps with an existing availability range."
            )
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)




class ServiceTimeSlot(models.Model):
    """
    Defines WHAT TIME a service runs on a given available date.
    Handles capacity and booking limits.
    """
    availability = models.ForeignKey(
        ServiceAvailability,
        on_delete=models.CASCADE,
        related_name="time_slots"
    )

    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("start_time",)

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"



class Package(models.Model):
    """
    Package model tied to a Service. Operators create packages under their services.
    - name: short package name (e.g., "Solo Traveler")
    - description: optional longer desc
    - price: package-specific price (overrides service.price if provided)
    - duration_days: optional override in days
    - is_active: allow operator to hide package without deleting
    - created_at/updated_at timestamps in ISO 8601 (Django default)
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Optional duration override in days")
    max_people = models.PositiveIntegerField(null=True, blank=True, help_text="Optional max capacity")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = ('service', 'name')  # prevent duplicate package names per service

    def __str__(self):
        return f"{self.name} ({self.service.title})"