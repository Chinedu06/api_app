from rest_framework import permissions


from rest_framework.permissions import BasePermission, SAFE_METHODS


class ServicePermission(BasePermission):

    def has_permission(self, request, view):
        # Always allow OPTIONS
        if request.method == "OPTIONS":
            return True

        # Public can read
        if request.method in SAFE_METHODS:
            return True

        # Must be authenticated to write
        if not request.user or not request.user.is_authenticated:
            return False

        # Operators & admins can create
        return request.user.is_staff or getattr(request.user, "role", None) == "operator"

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_staff
            or request.user.is_superuser
            or obj.operator == request.user
        )


class PackagePermission(permissions.BasePermission):
    """
    Packages Permission Rules:

    READ (GET):
    - Public users can read packages tied to active services

    WRITE (POST, PUT, PATCH, DELETE):
    - Operators can manage packages ONLY under their services
    - Admin can manage ALL packages
    """

    def has_permission(self, request, view):
        # READ access
        if request.method in permissions.SAFE_METHODS:
            return True

        # WRITE requires authentication
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator only
        return getattr(request.user, "role", None) == "operator"

    def has_object_permission(self, request, view, obj):
        # READ access
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator owns parent service
        return obj.service.operator_id == request.user.id
