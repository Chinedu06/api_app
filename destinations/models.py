from django.db import models


class Destination(models.Model):
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "country", "city")
        constraints = [
            models.UniqueConstraint(
                fields=["city", "country"],
                name="unique_destination_city_country",
            )
        ]

    def __str__(self):
        return f"{self.city}, {self.country}"