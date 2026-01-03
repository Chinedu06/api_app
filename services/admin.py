from django.contrib import admin
from .models import Service, Package
from django.contrib import admin
from .models import Service, ServiceImage, Package

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    readonly_fields = ("uploaded_at",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "operator",
        "is_active",
        "is_approved",
        "created_at",
    )
    list_filter = ("is_active", "is_approved", "created_at")
    search_fields = ("title", "operator__email", "slug", "description")
    ordering = ("-created_at",)
    readonly_fields = ("operator", "slug", "created_at")

    actions = ["approve_services", "reject_services"]

    inlines = [ServiceImageInline]

    def approve_services(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(
            request,
            f"{queryset.count()} service(s) approved successfully."
        )

    approve_services.short_description = "Approve selected services"

    def reject_services(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(
            request,
            f"{queryset.count()} service(s) rejected."
        )

    reject_services.short_description = "Reject selected services"



@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "duration_days", "is_active")
    list_filter = ("is_active", "service")
    search_fields = ("name", "service__title")
    ordering = ("service", "name")

def save_model(self, request, obj, form, change):
    if not change and not obj.operator:
        obj.operator = request.user
    super().save_model(request, obj, form, change)
