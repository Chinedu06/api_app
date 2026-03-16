from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model

from .models import User, SupplierProfile
from .emails import email_operator_approved


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_verified", "is_staff", "is_superuser")
    list_filter = ("role", "is_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number")}),
        ("Role & verification", {"fields": ("role", "is_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "role", "password1", "password2", "is_verified"),
        }),
    )

    def save_model(self, request, obj, form, change):
        should_send_approval_email = False

        if change and obj.pk:
            old_obj = User.objects.get(pk=obj.pk)
            if (
                old_obj.role == User.ROLE_OPERATOR
                and not old_obj.is_verified
                and obj.is_verified
            ):
                should_send_approval_email = True

        super().save_model(request, obj, form, change)

        if should_send_approval_email:
            email_operator_approved(obj)


User = get_user_model()


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "trading_name", "company_name", "created_at")
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("user__username", "trading_name", "company_name", "registration_number")