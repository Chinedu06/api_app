from django.contrib import admin
from .models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "country", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active", "country")
    search_fields = ("city", "country")
    ordering = ("sort_order", "country", "city")