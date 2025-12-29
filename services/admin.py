from django.contrib import admin
from .models import Service, Package


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "duration_days", "is_active")
    list_filter = ("is_active", "service")
    search_fields = ("name", "service__title")
    ordering = ("service", "name")
