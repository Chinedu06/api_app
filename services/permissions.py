from rest_framework import permissions


class ServicePermission(permissions.BasePermission):
    """
    Services Permission Rules:

    READ (GET):
    - Public users can read active services only
    - Operators can read their own services
    - Admin can read all services

    WRITE (POST, PUT, PATCH, DELETE):
    - Operators can manage ONLY their own services
    - Admin can manage ALL services
    """

    def has_permission(self, request, view):
        # READ access (public)
        if request.method in permissions.SAFE_METHODS:
            return True

        # WRITE access
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
            return obj.is_active and obj.is_approved

        # Admin override
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Operator owns the service
        return getattr(obj, "operator_id", None) == request.user.id

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
